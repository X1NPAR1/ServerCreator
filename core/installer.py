"""
Installation orchestration.

:class:`InstallerWorker` is a :class:`QThread` that performs the full server
installation off the UI thread, reporting progress and log lines through Qt
signals. It depends only on :mod:`PyQt6.QtCore` (no widgets), keeping it free of
presentation concerns.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core import downloader, server_configurator
from core.session import ServerSession
from core.version_manager import ResolvedDownload, VersionManager

_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# Log levels used by the UI to colour-code lines.
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
SUCCESS = "SUCCESS"


class InstallerWorker(QThread):
    """Runs the installation pipeline and emits progress to the UI."""

    # level, message
    log = pyqtSignal(str, str)
    # downloaded bytes, total bytes (0 when unknown)
    progress = pyqtSignal(int, int)
    # success flag, final message
    finished_install = pyqtSignal(bool, str)

    def __init__(self, session: ServerSession, language: str, parent=None) -> None:
        super().__init__(parent)
        self._session = session
        self._language = language
        self._version_manager = VersionManager()
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation; checked between steps."""
        self._cancelled = True

    # ------------------------------------------------------------------ helpers
    def _emit(self, level: str, message: str) -> None:
        self.log.emit(level, message)

    def _check_cancel(self) -> None:
        if self._cancelled:
            raise RuntimeError("cancelled")

    def _run_java(self, args: list[str], cwd: str, timeout: int = 600) -> subprocess.CompletedProcess:
        """Run a ``java`` command in ``cwd`` and return the completed process."""
        return subprocess.run(
            ["java"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=_NO_WINDOW,
        )

    # ----------------------------------------------------------------- pipeline
    def run(self) -> None:  # noqa: D401 (QThread entry point)
        """Execute the installation pipeline."""
        path = self._session.install_path
        try:
            self._create_directory(path)
            self._check_cancel()

            resolved = self._resolve(path)
            self._check_cancel()

            jar_name = self._download(resolved, path)
            self._check_cancel()

            self._verify(resolved, os.path.join(path, jar_name))
            self._check_cancel()

            server_jar = self._prepare_server(resolved, jar_name, path)
            self._check_cancel()

            self._first_run(server_jar, path)
            self._check_cancel()

            self._accept_eula(path)
            self._check_cancel()

            self._generate_properties(server_jar, path)
            self._check_cancel()

            self._apply_properties(path)
            self._check_cancel()

            self._write_scripts(path, server_jar)

            self._emit(SUCCESS, "log_done")
            self.finished_install.emit(True, server_jar)
        except RuntimeError:
            self.finished_install.emit(False, "cancelled")
        except Exception as exc:  # noqa: BLE001 — surfaced to the user
            self._emit(ERROR, str(exc))
            self.finished_install.emit(False, str(exc))

    # --------------------------------------------------------------- steps
    def _create_directory(self, path: str) -> None:
        self._emit(INFO, f"::log_creating_dir::{path}")
        os.makedirs(path, exist_ok=True)

    def _resolve(self, path: str) -> ResolvedDownload:
        resolved = self._version_manager.resolve_download(
            self._session.platform, self._session.mc_version
        )
        if resolved.note:
            self._emit(INFO, resolved.note)
        return resolved

    def _download(self, resolved: ResolvedDownload, path: str) -> str:
        self._emit(INFO, f"::log_downloading::{resolved.filename}")
        dest = os.path.join(path, resolved.filename)
        downloader.download_file(
            resolved.url,
            dest,
            progress_callback=lambda d, t: self.progress.emit(d, t),
        )
        self._emit(SUCCESS, f"::log_downloading::{resolved.filename}")
        return resolved.filename

    def _verify(self, resolved: ResolvedDownload, file_path: str) -> None:
        if not resolved.checksum:
            self._emit(WARNING, "log_verify_skip")
            return
        self._emit(INFO, "log_verifying")
        if not downloader.verify_checksum(file_path, resolved.checksum, resolved.algorithm):
            try:
                os.remove(file_path)
            except OSError:
                pass
            raise RuntimeError("Checksum verification failed for the downloaded file.")
        self._emit(SUCCESS, "log_verifying")

    def _prepare_server(self, resolved: ResolvedDownload, jar_name: str, path: str) -> str:
        """
        Turn an installer artifact into a runnable server jar where required.

        For Vanilla/Paper/Purpur/Fabric the downloaded jar is already the
        server. For Forge/NeoForge the installer is executed; for
        Spigot/CraftBukkit BuildTools is run to compile the server.
        """
        if not resolved.is_installer:
            return jar_name

        self._emit(INFO, resolved.note or "Running installer")
        if jar_name == "BuildTools.jar":
            target = "spigot" if self._session.platform == "spigot" else "craftbukkit"
            result = self._run_java(
                ["-jar", "BuildTools.jar", "--rev", self._session.mc_version, "--compile", target],
                cwd=path,
                timeout=2400,
            )
            if result.returncode != 0:
                raise RuntimeError(f"BuildTools failed:\n{result.stderr[-2000:]}")
            produced = self._find_first(path, prefix=target, suffix=".jar")
            if not produced:
                raise RuntimeError("BuildTools did not produce a server jar.")
            shutil.move(os.path.join(path, produced), os.path.join(path, "server.jar"))
            return "server.jar"

        # Forge / NeoForge installer.
        result = self._run_java(["-jar", jar_name, "--installServer"], cwd=path, timeout=1800)
        if result.returncode != 0:
            raise RuntimeError(f"Installer failed:\n{result.stderr[-2000:]}")
        run_jar = self._find_first(path, prefix=self._session.platform, suffix=".jar")
        return run_jar or jar_name

    def _first_run(self, server_jar: str, path: str) -> None:
        self._emit(INFO, "log_running_first")
        # The first run exits immediately because the EULA has not been accepted.
        self._run_java(
            [f"-Xmx{self._session.xmx_mb}M", "-jar", server_jar, "nogui"],
            cwd=path,
            timeout=300,
        )

    def _accept_eula(self, path: str) -> None:
        self._emit(INFO, "log_eula")
        if not server_configurator.accept_eula(path):
            raise RuntimeError("Failed to write eula.txt")

    def _generate_properties(self, server_jar: str, path: str) -> None:
        if os.path.exists(os.path.join(path, "server.properties")):
            return
        self._emit(INFO, "log_configuring")
        self._run_java(
            [f"-Xmx{self._session.xmx_mb}M", "-jar", server_jar, "nogui"],
            cwd=path,
            timeout=420,
        )

    def _apply_properties(self, path: str) -> None:
        self._emit(INFO, "log_editing")
        if not server_configurator.apply_server_properties(path, self._session, self._language):
            raise RuntimeError("Failed to write server.properties")
        self._emit(INFO, "log_motd")

    def _write_scripts(self, path: str, server_jar: str) -> None:
        if not self._session.generate_start_script:
            return
        self._emit(INFO, "log_scripts")
        server_configurator.write_start_scripts(path, self._session, server_jar)

    @staticmethod
    def _find_first(path: str, prefix: str, suffix: str) -> Optional[str]:
        for name in sorted(os.listdir(path)):
            lower = name.lower()
            if lower.startswith(prefix.lower()) and lower.endswith(suffix.lower()):
                return name
        return None
