"""
Shared helper utilities for ServerCreator.

This module intentionally has no dependencies on the user interface so that it
can be imported safely from both the GUI and the background worker threads.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from typing import Any


# --------------------------------------------------------------------------- #
# Resource resolution                                                         #
# --------------------------------------------------------------------------- #
def get_asset_path(relative_path: str) -> str:
    """
    Resolve a path to a bundled resource.

    Works transparently both when running from source and when packaged with
    PyInstaller (where bundled data lives under ``sys._MEIPASS``).

    Args:
        relative_path: Path of the resource relative to the project root,
            for example ``"assets/logo.ico"``.

    Returns:
        An absolute filesystem path to the resource.
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def logo_path() -> str:
    """Return the absolute path to the application logo/icon."""
    return get_asset_path(os.path.join("assets", "logo.ico"))


# --------------------------------------------------------------------------- #
# Per-user application data                                                   #
# --------------------------------------------------------------------------- #
def app_data_dir() -> str:
    """
    Return the per-user data directory for ServerCreator.

    On Windows this resolves to ``%APPDATA%\\ServerCreator``. On other
    platforms a sensible hidden directory inside the user's home folder is
    used. The directory is created if it does not yet exist.
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        directory = os.path.join(base, "ServerCreator")
    else:
        directory = os.path.join(os.path.expanduser("~"), ".servercreator")
    os.makedirs(directory, exist_ok=True)
    return directory


def config_path() -> str:
    """Return the absolute path to ``config.json`` inside the data directory."""
    return os.path.join(app_data_dir(), "config.json")


def version_cache_path() -> str:
    """Return the absolute path to the version cache file."""
    return os.path.join(app_data_dir(), "version_cache.json")


def default_servers_dir() -> str:
    """Return the default base directory in which servers are installed."""
    directory = os.path.join(app_data_dir(), "Servers")
    os.makedirs(directory, exist_ok=True)
    return directory


# --------------------------------------------------------------------------- #
# Atomic JSON persistence                                                     #
# --------------------------------------------------------------------------- #
def read_json(path: str, default: Any = None) -> Any:
    """
    Read and parse a JSON file, returning ``default`` on any failure.

    The function never raises; a missing or corrupt file simply yields the
    provided default value.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def write_json(path: str, data: Any) -> bool:
    """
    Write ``data`` to ``path`` as UTF-8 JSON using an atomic replace.

    The content is first written to a temporary file in the same directory and
    then atomically moved into place, which prevents partially written or
    corrupt configuration files if the process is interrupted.

    Returns:
        ``True`` on success, ``False`` otherwise.
    """
    try:
        directory = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            shutil.move(tmp_path, path)
            return True
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
    except OSError:
        return False


# --------------------------------------------------------------------------- #
# Filesystem helpers                                                          #
# --------------------------------------------------------------------------- #
def free_space_bytes(path: str) -> int:
    """
    Return the number of free bytes available on the volume that ``path`` lives
    on. Falls back to the nearest existing parent directory if ``path`` itself
    does not yet exist. Returns ``0`` when the value cannot be determined.
    """
    probe = path
    while probe and not os.path.exists(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    try:
        return shutil.disk_usage(probe or os.path.abspath(os.sep)).free
    except OSError:
        return 0


def human_readable_size(num_bytes: float) -> str:
    """Convert a byte count into a human readable string (e.g. ``"12.3 MB"``)."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"
