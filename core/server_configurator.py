"""
Generation and editing of ``eula.txt``, ``server.properties`` and start scripts.
"""

from __future__ import annotations

import os
from typing import Dict

from core.session import ServerSession

# Aikar's flags — a widely used G1GC tuning preset for Minecraft servers.
AIKAR_FLAGS = (
    "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 "
    "-XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC "
    "-XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 "
    "-XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 "
    "-XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 "
    "-XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 "
    "-XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1"
)


def accept_eula(install_path: str) -> bool:
    """
    Set ``eula=true`` in ``eula.txt``, creating the file if necessary.

    Returns ``True`` on success.
    """
    eula_file = os.path.join(install_path, "eula.txt")
    try:
        if os.path.exists(eula_file):
            with open(eula_file, "r", encoding="utf-8") as handle:
                content = handle.read()
            content = content.replace("eula=false", "eula=true")
            if "eula=true" not in content:
                content += "\neula=true\n"
        else:
            content = "eula=true\n"
        with open(eula_file, "w", encoding="utf-8") as handle:
            handle.write(content)
        return True
    except OSError:
        return False


def motd_for_language(language: str) -> str:
    """Return the branded MOTD string for the given UI language."""
    if language == "tr":
        return "\\u00A7fBu sunucu \\u00A7aServerCreator\\u00A7f tarafından oluşturulmuştur."
    return "\\u00A7fThis server was created by \\u00A7aServerCreator\\u00A7f."


def _properties_from_session(session: ServerSession, language: str) -> Dict[str, str]:
    """Build the key/value map written to ``server.properties``."""
    return {
        "online-mode": "true" if session.online_mode else "false",
        "max-players": str(session.max_players),
        "gamemode": session.gamemode,
        "hardcore": "true" if session.hardcore else "false",
        "white-list": "true" if session.whitelist else "false",
        "server-port": str(session.server_port),
        "pvp": "true" if session.pvp else "false",
        "allow-nether": "true" if session.allow_nether else "false",
        "level-seed": session.level_seed,
        "motd": motd_for_language(language),
    }


def apply_server_properties(install_path: str, session: ServerSession, language: str) -> bool:
    """
    Update (or create) ``server.properties`` with the user's choices.

    Existing keys are overwritten in place; missing keys are appended. If the
    file does not exist a complete file is generated from the session values.

    Returns ``True`` on success.
    """
    props_file = os.path.join(install_path, "server.properties")
    overrides = _properties_from_session(session, language)
    try:
        lines: list[str] = []
        seen: set[str] = set()
        if os.path.exists(props_file):
            with open(props_file, "r", encoding="utf-8") as handle:
                for raw in handle.read().splitlines():
                    stripped = raw.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        lines.append(raw)
                        continue
                    key = stripped.split("=", 1)[0]
                    if key in overrides:
                        lines.append(f"{key}={overrides[key]}")
                        seen.add(key)
                    else:
                        lines.append(raw)
        for key, value in overrides.items():
            if key not in seen:
                lines.append(f"{key}={value}")
        with open(props_file, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        return True
    except OSError:
        return False


def read_properties(install_path: str) -> dict:
    """
    Read ``server.properties`` into an ordered ``dict``.

    Comment and blank lines are ignored. Returns an empty dict if the file does
    not exist or cannot be read.
    """
    result: dict = {}
    path = os.path.join(install_path, "server.properties")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for raw in handle.read().splitlines():
                stripped = raw.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                result[key.strip()] = value
    except OSError:
        pass
    return result


def write_properties(install_path: str, overrides: dict) -> bool:
    """
    Merge ``overrides`` into ``server.properties``, preserving existing keys,
    comments and ordering. Missing keys are appended. Returns ``True`` on
    success.
    """
    path = os.path.join(install_path, "server.properties")
    try:
        lines: list[str] = []
        seen: set[str] = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                for raw in handle.read().splitlines():
                    stripped = raw.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        lines.append(raw)
                        continue
                    key = stripped.split("=", 1)[0].strip()
                    if key in overrides:
                        lines.append(f"{key}={overrides[key]}")
                        seen.add(key)
                    else:
                        lines.append(raw)
        for key, value in overrides.items():
            if key not in seen:
                lines.append(f"{key}={value}")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        return True
    except OSError:
        return False


def jvm_flags(session) -> str:
    """Return the JVM flag string for the session (empty if disabled)."""
    return AIKAR_FLAGS if session.use_aikar_flags else ""


def write_start_scripts(install_path: str, session: ServerSession, jar_name: str = "server.jar") -> bool:
    """
    Write ``start.bat`` (Windows) and ``start.sh`` (Unix) launchers.

    Returns ``True`` on success.
    """
    flags = jvm_flags(session)
    name = session.server_name
    bat = (
        "@echo off\r\n"
        "chcp 65001 > nul\r\n"
        f"title {name} - Minecraft Server (ServerCreator)\r\n"
        f"echo [ServerCreator] \"{name}\" sunucusu baslatiliyor...\r\n"
        f"java -Xms{session.xms_mb}M -Xmx{session.xmx_mb}M {flags} -jar {jar_name} nogui\r\n"
        "pause\r\n"
    )
    sh = (
        "#!/usr/bin/env bash\n"
        f"# Start script generated by ServerCreator for \"{name}\".\n"
        f"java -Xms{session.xms_mb}M -Xmx{session.xmx_mb}M {flags} -jar {jar_name} nogui\n"
    )
    try:
        with open(os.path.join(install_path, "start.bat"), "w", encoding="utf-8") as handle:
            handle.write(bat)
        sh_path = os.path.join(install_path, "start.sh")
        with open(sh_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(sh)
        try:
            os.chmod(sh_path, 0o755)
        except OSError:
            pass
        return True
    except OSError:
        return False
