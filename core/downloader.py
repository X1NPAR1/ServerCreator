"""
Robust HTTP helpers: JSON fetching with retries and streamed file downloads.

All network access in the application funnels through this module so that
timeout, retry and back-off behaviour is implemented in exactly one place.
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Callable, Optional

import requests

DEFAULT_TIMEOUT = 20  # seconds
DEFAULT_RETRIES = 3
USER_AGENT = "ServerCreator/1.76.3 (+https://github.com/X1NPAR1)"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})


class DownloadError(Exception):
    """Raised when a download fails after exhausting all retries."""


def fetch_json(url: str, timeout: int = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES) -> Any:
    """
    Fetch and decode a JSON document with exponential back-off.

    Raises:
        DownloadError: if every attempt fails.
    """
    last_error: Optional[Exception] = None
    for attempt in range(retries):
        try:
            response = _SESSION.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise DownloadError(f"Failed to fetch {url}: {last_error}")


def fetch_text(url: str, timeout: int = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES) -> str:
    """Fetch a text document with exponential back-off."""
    last_error: Optional[Exception] = None
    for attempt in range(retries):
        try:
            response = _SESSION.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise DownloadError(f"Failed to fetch {url}: {last_error}")


def download_file(
    url: str,
    destination: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    timeout: int = 60,
) -> str:
    """
    Stream a remote file to ``destination`` atomically.

    The content is written to a ``.part`` file first and only renamed into
    place once the transfer completes successfully. A partial transfer leaves
    no corrupt file behind.

    Args:
        url: The remote URL to download.
        destination: Target filesystem path.
        progress_callback: Optional callback invoked as
            ``callback(downloaded_bytes, total_bytes)``; ``total_bytes`` is 0
            when the server does not report a content length.

    Returns:
        The destination path.

    Raises:
        DownloadError: on any failure; the partial file is removed.
    """
    part_path = destination + ".part"
    try:
        with _SESSION.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
            with open(part_path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback is not None:
                        progress_callback(downloaded, total)
        os.replace(part_path, destination)
        return destination
    except (requests.RequestException, OSError) as exc:
        if os.path.exists(part_path):
            try:
                os.remove(part_path)
            except OSError:
                pass
        raise DownloadError(f"Failed to download {url}: {exc}") from exc


def verify_checksum(path: str, expected: str, algorithm: str = "sha256") -> bool:
    """
    Verify that ``path`` matches ``expected`` using the given hash algorithm.

    The comparison is case-insensitive. Returns ``False`` if the file cannot be
    read or the algorithm is unknown.
    """
    try:
        digest = hashlib.new(algorithm)
    except ValueError:
        return False
    try:
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError:
        return False
    return digest.hexdigest().lower() == expected.strip().lower()
