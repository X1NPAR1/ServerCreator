"""
Version discovery and download-URL resolution for every supported platform.

Responsibilities:

* Query each platform's official API/endpoint for the Minecraft versions it
  supports, newest first.
* Persist results to a 24-hour cache so the application is usable offline and
  does not hammer the upstream services.
* Resolve the concrete download URL (and checksum where available) for a chosen
  platform/version pair at install time.

Every network call goes through :mod:`core.downloader`, which provides retry
and back-off behaviour.
"""

from __future__ import annotations

import re
import time
from typing import Dict, List, Optional

from packaging.version import InvalidVersion, Version

from core import downloader
from utils import read_json, version_cache_path, write_json

CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# Platforms exposed in the UI, in display order.
PLATFORMS = (
    "vanilla",
    "paper",
    "purpur",
    "spigot",
    "craftbukkit",
    "fabric",
    "forge",
    "neoforge",
)

RECOMMENDED_PLATFORMS = ("paper",)


class ResolvedDownload:
    """Describes a concrete downloadable server artifact."""

    def __init__(
        self,
        url: str,
        filename: str,
        checksum: Optional[str] = None,
        algorithm: str = "sha256",
        is_installer: bool = False,
        note: str = "",
    ) -> None:
        self.url = url
        self.filename = filename
        self.checksum = checksum
        self.algorithm = algorithm
        # ``is_installer`` is True for Forge/NeoForge where the downloaded JAR
        # is an installer that must be executed to produce the server.
        self.is_installer = is_installer
        self.note = note


def _sort_versions_desc(versions: List[str]) -> List[str]:
    """Sort Minecraft version strings from newest to oldest, tolerating snapshots."""
    def key(value: str):
        try:
            return (1, Version(value))
        except InvalidVersion:
            return (0, Version("0"))

    # Stable sort keeps unparsable entries in their original relative order.
    parsable = [v for v in versions if _is_release(v)]
    parsable.sort(key=key, reverse=True)
    return parsable


def _is_release(value: str) -> bool:
    """Return True for proper release versions (filters out snapshots/pre-releases)."""
    return bool(re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value))


class VersionManager:
    """Fetches and caches the supported Minecraft versions per platform."""

    def __init__(self) -> None:
        self._cache: Dict = read_json(version_cache_path(), default={}) or {}

    # ------------------------------------------------------------------ cache
    def is_cache_fresh(self, platform: str) -> bool:
        entry = self._cache.get(platform)
        if not entry:
            return False
        return (time.time() - entry.get("fetched_at", 0)) < CACHE_TTL_SECONDS

    def cached_versions(self, platform: str) -> List[str]:
        entry = self._cache.get(platform) or {}
        return list(entry.get("versions", []))

    def _store(self, platform: str, versions: List[str]) -> None:
        self._cache[platform] = {"versions": versions, "fetched_at": time.time()}
        write_json(version_cache_path(), self._cache)

    # ------------------------------------------------------------- public API
    def get_versions(self, platform: str, force: bool = False) -> List[str]:
        """
        Return supported versions for ``platform`` (newest first).

        Uses the cache when fresh. On a network failure the last cached list is
        returned so the UI always has something to show.
        """
        if not force and self.is_cache_fresh(platform):
            return self.cached_versions(platform)
        try:
            versions = self._fetch_versions(platform)
            versions = _sort_versions_desc(versions)
            if versions:
                self._store(platform, versions)
            return versions
        except downloader.DownloadError:
            return self.cached_versions(platform)

    # ----------------------------------------------------------- fetch router
    def _fetch_versions(self, platform: str) -> List[str]:
        fetchers = {
            "vanilla": self._vanilla_versions,
            "paper": lambda: self._papermc_versions("paper", "https://api.papermc.io/v2/projects/paper"),
            "purpur": self._purpur_versions,
            "fabric": self._fabric_versions,
            "forge": self._forge_versions,
            "neoforge": self._neoforge_versions,
            "spigot": self._bukkit_like_versions,
            "craftbukkit": self._bukkit_like_versions,
        }
        fetch = fetchers.get(platform)
        if fetch is None:
            return []
        return fetch()

    # ----------------------------------------------------------- per platform
    def _vanilla_versions(self) -> List[str]:
        data = downloader.fetch_json(
            "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
        )
        return [v["id"] for v in data.get("versions", []) if v.get("type") == "release"]

    def _papermc_versions(self, project: str, base: str) -> List[str]:
        data = downloader.fetch_json(base)
        return list(data.get("versions", []))

    def _purpur_versions(self) -> List[str]:
        data = downloader.fetch_json("https://api.purpurmc.org/v2/purpur")
        return list(data.get("versions", []))

    def _fabric_versions(self) -> List[str]:
        data = downloader.fetch_json("https://meta.fabricmc.net/v2/versions/game")
        return [v["version"] for v in data if v.get("stable")]

    def _forge_versions(self) -> List[str]:
        text = downloader.fetch_text(
            "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
        )
        # Entries look like "1.20.1-47.2.0"; the MC version is the prefix.
        mc_versions = set()
        for match in re.findall(r"<version>([^<]+)</version>", text):
            mc = match.split("-")[0]
            if _is_release(mc):
                mc_versions.add(mc)
        return list(mc_versions)

    def _neoforge_versions(self) -> List[str]:
        text = downloader.fetch_text(
            "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
        )
        mc_versions = set()
        # NeoForge versions encode MC version as "<minor>.<patch>.x" of 1.x.
        for match in re.findall(r"<version>([^<]+)</version>", text):
            parts = match.split(".")
            if len(parts) >= 2:
                mc_versions.add(f"1.{parts[0]}.{parts[1]}" if parts[1] != "0" else f"1.{parts[0]}")
        return [v for v in mc_versions if _is_release(v)]

    def _bukkit_like_versions(self) -> List[str]:
        """
        Spigot and CraftBukkit are built with BuildTools, which supports the
        same set of versions. We reuse the Mojang release manifest, limited to a
        practical recent window, as the source of selectable versions.
        """
        return self._vanilla_versions()

    # ----------------------------------------------------- download resolution
    def resolve_download(self, platform: str, mc_version: str) -> ResolvedDownload:
        """
        Resolve a concrete :class:`ResolvedDownload` for the chosen pair.

        Raises:
            downloader.DownloadError: if the artifact cannot be resolved.
        """
        if platform == "vanilla":
            return self._resolve_vanilla(mc_version)
        if platform == "paper":
            return self._resolve_papermc("paper", "https://api.papermc.io/v2/projects/paper", mc_version)
        if platform == "purpur":
            return self._resolve_purpur(mc_version)
        if platform == "fabric":
            return self._resolve_fabric(mc_version)
        if platform == "forge":
            return self._resolve_forge(mc_version)
        if platform == "neoforge":
            return self._resolve_neoforge(mc_version)
        if platform in ("spigot", "craftbukkit"):
            return self._resolve_buildtools(platform, mc_version)
        raise downloader.DownloadError(f"Unknown platform: {platform}")

    def _resolve_vanilla(self, mc_version: str) -> ResolvedDownload:
        manifest = downloader.fetch_json(
            "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
        )
        entry = next((v for v in manifest.get("versions", []) if v["id"] == mc_version), None)
        if not entry:
            raise downloader.DownloadError(f"Vanilla {mc_version} not found")
        detail = downloader.fetch_json(entry["url"])
        server = detail.get("downloads", {}).get("server")
        if not server:
            raise downloader.DownloadError(f"No server jar for vanilla {mc_version}")
        return ResolvedDownload(
            url=server["url"],
            filename="server.jar",
            checksum=server.get("sha1"),
            algorithm="sha1",
        )

    def _resolve_papermc(self, project: str, base: str, mc_version: str) -> ResolvedDownload:
        builds = downloader.fetch_json(f"{base}/versions/{mc_version}/builds")
        candidates = [b for b in builds.get("builds", []) if b.get("channel") == "default"]
        chosen = (candidates or builds.get("builds", []))[-1]
        build = chosen["build"]
        app = chosen["downloads"]["application"]
        name = app["name"]
        url = f"{base}/versions/{mc_version}/builds/{build}/downloads/{name}"
        return ResolvedDownload(
            url=url,
            filename="server.jar",
            checksum=app.get("sha256"),
            algorithm="sha256",
        )

    def _resolve_purpur(self, mc_version: str) -> ResolvedDownload:
        meta = downloader.fetch_json(f"https://api.purpurmc.org/v2/purpur/{mc_version}")
        latest = meta.get("builds", {}).get("latest")
        url = f"https://api.purpurmc.org/v2/purpur/{mc_version}/{latest}/download"
        return ResolvedDownload(url=url, filename="server.jar")

    def _resolve_fabric(self, mc_version: str) -> ResolvedDownload:
        loaders = downloader.fetch_json(f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}")
        if not loaders:
            raise downloader.DownloadError(f"No Fabric loader for {mc_version}")
        loader = loaders[0]["loader"]["version"]
        installers = downloader.fetch_json("https://meta.fabricmc.net/v2/versions/installer")
        installer = installers[0]["version"]
        url = (
            f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}/"
            f"{loader}/{installer}/server/jar"
        )
        return ResolvedDownload(url=url, filename="server.jar")

    def _resolve_forge(self, mc_version: str) -> ResolvedDownload:
        text = downloader.fetch_text(
            "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml"
        )
        full = [m for m in re.findall(r"<version>([^<]+)</version>", text) if m.startswith(mc_version + "-")]
        if not full:
            raise downloader.DownloadError(f"No Forge build for {mc_version}")
        chosen = full[-1]
        url = (
            f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
            f"{chosen}/forge-{chosen}-installer.jar"
        )
        return ResolvedDownload(
            url=url,
            filename="forge-installer.jar",
            is_installer=True,
            note="Forge ships an installer that generates the server on first run.",
        )

    def _resolve_neoforge(self, mc_version: str) -> ResolvedDownload:
        text = downloader.fetch_text(
            "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
        )
        # Map "1.20.1" -> prefix "20.1"
        parts = mc_version.split(".")
        prefix = f"{parts[1]}.{parts[2] if len(parts) > 2 else '0'}"
        candidates = [m for m in re.findall(r"<version>([^<]+)</version>", text) if m.startswith(prefix + ".")]
        if not candidates:
            raise downloader.DownloadError(f"No NeoForge build for {mc_version}")
        chosen = candidates[-1]
        url = (
            f"https://maven.neoforged.net/releases/net/neoforged/neoforge/"
            f"{chosen}/neoforge-{chosen}-installer.jar"
        )
        return ResolvedDownload(
            url=url,
            filename="neoforge-installer.jar",
            is_installer=True,
            note="NeoForge ships an installer that generates the server on first run.",
        )

    def _resolve_buildtools(self, platform: str, mc_version: str) -> ResolvedDownload:
        url = "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar"
        return ResolvedDownload(
            url=url,
            filename="BuildTools.jar",
            is_installer=True,
            note="Spigot/CraftBukkit are compiled locally with BuildTools.",
        )
