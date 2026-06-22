"""
Java detection and version-requirement resolution.

This module determines which Java major version a given Minecraft release
requires and inspects the local system for an installed Java runtime.
"""

from __future__ import annotations

import glob
import os
import platform
import re
import subprocess
import sys
import zipfile
from typing import Callable, Optional, Tuple

from packaging.version import InvalidVersion, Version

from utils import app_data_dir

# Official download page shown to the user when Java is missing or outdated.
JAVA_DOWNLOAD_URL = "https://adoptium.net/temurin/releases/"

# Hide the console window when invoking ``java`` on Windows.
_NO_WINDOW = 0x08000000 if hasattr(subprocess, "STARTUPINFO") else 0


def required_java_for(mc_version: str) -> int:
    """
    Return the minimum Java major version required by ``mc_version``.

    The thresholds follow Mojang's published requirements:

    * Minecraft 1.20.5 and newer require Java 21.
    * Minecraft 1.18 through 1.20.4 require Java 17.
    * Minecraft 1.17.x requires Java 16.
    * Older versions run on Java 8.
    """
    try:
        version = Version(mc_version)
    except InvalidVersion:
        return 8

    if version >= Version("1.20.5"):
        return 21
    if version >= Version("1.18"):
        return 17
    if version >= Version("1.17"):
        return 16
    return 8


def detect_java() -> Tuple[bool, Optional[int], str]:
    """
    Detect the Java runtime available on ``PATH``.

    Returns a tuple ``(found, major_version, raw_output)`` where ``found`` is
    ``True`` when a ``java`` executable responded, ``major_version`` is the
    parsed major version (or ``None`` if it could not be parsed) and
    ``raw_output`` is the trimmed version banner for diagnostics.
    """
    try:
        completed = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return False, None, ""

    # ``java -version`` prints to stderr on most distributions.
    output = (completed.stderr or "") + (completed.stdout or "")
    output = output.strip()
    if not output:
        return False, None, ""

    return True, _parse_major(output), output


def _parse_major(banner: str) -> Optional[int]:
    """Extract the Java major version number from a ``java -version`` banner."""
    match = re.search(r'version "?(\d+)(?:\.(\d+))?', banner)
    if not match:
        return None
    major = int(match.group(1))
    # Legacy scheme: "1.8.0_xxx" means Java 8.
    if major == 1 and match.group(2):
        return int(match.group(2))
    return major


# --------------------------------------------------------------------------- #
# Bundled JDK management (automatic installation)                             #
# --------------------------------------------------------------------------- #
def _java_root(major: int) -> str:
    """Return the directory where a bundled JDK of ``major`` is installed."""
    return os.path.join(app_data_dir(), "java", str(major))


def bundled_java_exe(major: int) -> Optional[str]:
    """
    Return the path to a previously installed bundled ``java`` executable for
    ``major``, or ``None`` if one is not present.
    """
    root = _java_root(major)
    exe = "java.exe" if sys.platform.startswith("win") else "java"
    matches = glob.glob(os.path.join(root, "**", "bin", exe), recursive=True)
    return matches[0] if matches else None


def resolve_java(required_major: int) -> Optional[str]:
    """
    Return a usable ``java`` command for ``required_major`` without installing.

    Preference order: a system Java new enough for the requirement, then a
    previously bundled JDK. Returns ``None`` when neither is available, which
    signals the caller to install one via :func:`install_java`.
    """
    found, major, _ = detect_java()
    if found and major is not None and major >= required_major:
        return "java"
    return bundled_java_exe(required_major)


def _adoptium_url(major: int) -> str:
    """Build the Adoptium (Eclipse Temurin) binary download URL for this OS."""
    arch = "x64"
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        arch = "aarch64"
    if sys.platform.startswith("win"):
        os_name = "windows"
    elif sys.platform == "darwin":
        os_name = "mac"
    else:
        os_name = "linux"
    return (
        f"https://api.adoptium.net/v3/binary/latest/{major}/ga/"
        f"{os_name}/{arch}/jdk/hotspot/normal/eclipse"
    )


def install_java(
    major: int,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Download and extract an Eclipse Temurin JDK for ``major`` into the per-user
    data directory and return the path to its ``java`` executable.

    Only the ``.zip`` distribution (Windows) is handled inline; on other
    platforms the archive is still extracted via :mod:`zipfile`/``tarfile``.

    Raises:
        RuntimeError: if the download or extraction fails or no executable is
            found afterwards.
    """
    # Imported lazily to avoid a hard dependency cycle at module import time.
    from core import downloader

    root = _java_root(major)
    os.makedirs(root, exist_ok=True)
    url = _adoptium_url(major)
    if log_callback:
        log_callback(f"Downloading Java {major} (Eclipse Temurin)…")

    is_zip = sys.platform.startswith("win")
    archive = os.path.join(root, f"jdk-{major}.{'zip' if is_zip else 'tar.gz'}")
    try:
        downloader.download_file(url, archive, progress_callback=progress_callback, timeout=120)
    except downloader.DownloadError as exc:
        raise RuntimeError(f"Failed to download Java {major}: {exc}") from exc

    if log_callback:
        log_callback(f"Extracting Java {major}…")
    try:
        if is_zip:
            with zipfile.ZipFile(archive, "r") as zf:
                zf.extractall(root)
        else:
            import tarfile

            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(root)
    except (OSError, zipfile.BadZipFile) as exc:
        raise RuntimeError(f"Failed to extract Java {major}: {exc}") from exc
    finally:
        try:
            os.remove(archive)
        except OSError:
            pass

    exe = bundled_java_exe(major)
    if not exe:
        raise RuntimeError(f"Java {major} executable not found after extraction.")
    if log_callback:
        log_callback(f"Java {major} is ready.")
    return exe
