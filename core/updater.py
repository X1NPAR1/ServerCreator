"""
Automatic update support.

On every launch the application asks GitHub for the latest published release in
the release repository. If the tag is newer than the running version the user
is offered an in-app update: the setup executable is downloaded and launched,
and the application exits so the installer can replace it.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from packaging.version import InvalidVersion, Version

from core import downloader
from version import APP_VERSION, releases_api_url


class UpdateChecker(QThread):
    """Background check for a newer published release."""

    # latest_version, download_url
    update_available = pyqtSignal(str, str)
    # emitted when no update is found or the check failed (silent)
    no_update = pyqtSignal()

    def run(self) -> None:  # noqa: D401
        try:
            data = downloader.fetch_json(releases_api_url(), timeout=10, retries=2)
        except downloader.DownloadError:
            self.no_update.emit()
            return

        tag = (data.get("tag_name") or "").lstrip("vV")
        asset_url = self._find_setup_asset(data)
        if not tag or not asset_url or not self._is_newer(tag):
            self.no_update.emit()
            return
        self.update_available.emit(tag, asset_url)

    @staticmethod
    def _find_setup_asset(data: dict) -> Optional[str]:
        """Return the download URL of the first ``.exe`` asset in the release."""
        for asset in data.get("assets", []):
            name = (asset.get("name") or "").lower()
            if name.endswith(".exe"):
                return asset.get("browser_download_url")
        return None

    @staticmethod
    def _is_newer(remote_tag: str) -> bool:
        try:
            return Version(remote_tag) > Version(APP_VERSION)
        except InvalidVersion:
            return False


class UpdateDownloader(QThread):
    """Downloads the setup executable to a temporary location."""

    progress = pyqtSignal(int, int)
    completed = pyqtSignal(str)   # path to the downloaded installer
    failed = pyqtSignal()

    def __init__(self, url: str, parent=None) -> None:
        super().__init__(parent)
        self._url = url

    def run(self) -> None:  # noqa: D401
        try:
            target = os.path.join(tempfile.gettempdir(), "ServerCreator-Update-Setup.exe")
            downloader.download_file(
                self._url,
                target,
                progress_callback=lambda d, t: self.progress.emit(d, t),
            )
            self.completed.emit(target)
        except downloader.DownloadError:
            self.failed.emit()


def launch_installer_and_exit(installer_path: str) -> None:
    """
    Start the downloaded installer and terminate the current application.

    The installer is launched detached so it survives the parent exiting, which
    is required for it to overwrite the running executable.
    """
    try:
        if sys.platform.startswith("win"):
            os.startfile(installer_path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen([installer_path])
    finally:
        sys.exit(0)
