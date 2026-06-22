"""
Java detection and version-requirement resolution.

This module determines which Java major version a given Minecraft release
requires and inspects the local system for an installed Java runtime.
"""

from __future__ import annotations

import re
import subprocess
from typing import Optional, Tuple

from packaging.version import InvalidVersion, Version

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
