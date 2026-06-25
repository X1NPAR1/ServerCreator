"""
Installation orchestration.

:class:`InstallerWorker` is a :class:`QThread` that performs the full server
installation off the UI thread, reporting progress and log lines through Qt
signals. It depends only on :mod:`PyQt6.QtCore` (no widgets).

Key behaviours:

* The download step reports real byte progress; long, open-ended steps
  (installing Java, compiling with BuildTools, the server's first run) switch
  the progress bar to a busy/indeterminate state and stream their console
  output live so the user always sees activity.
* The required Java runtime is detected and, if missing or too old, an Eclipse
  Temurin JDK is downloaded and used automatically.
* Build tooling (BuildTools for Spigot/CraftBukkit, Forge/NeoForge installers)
  runs in a throwaway subdirectory and all intermediate artifacts are removed,
  leaving only the final server jar and the files the server itself generates.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core import downloader, java_manager, server_configurator
from core.session import ServerSession
from core.version_manager import ResolvedDownload, VersionManager

_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# Matches the server's "Done (12.345s)! For help, type ..." readiness line.
_DONE_RE = re.compile(r"Done \([\d.]+s\)!")

# Log levels used by the UI to colour-code lines.
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
SUCCESS = "SUCCESS"

# Build artifacts left behind by BuildTools that must not pollute the server.
_BUILDTOOLS_JUNK = (
    "Bukkit", "CraftBukkit", "Spigot", "BuildData", "work",
    "apache-maven-3.6.0", "apache-maven-3.9.6", "BuildTools.jar",
    "BuildTools.log.txt", ".git",
)


class InstallerWorker(QThread):
    """Runs the installation pipeline and emits progress to the UI."""

    log = pyqtSignal(str, str)                 # level, message
    progress = pyqtSignal(int, int)            # downloaded, total (0 => unknown)
    busy = pyqtSignal(bool)                    # True => indeterminate phase
    finished_install = pyqtSignal(bool, str)   # success, server jar name (or error)

    def __init__(self, session: ServerSession, language: str, parent=None) -> None:
        super().__init__(parent)
        self._session = session
        self._language = language
        self._version_manager = VersionManager()
        self._cancelled = False
        self._java = "java"          # resolved java command, set during the run
        self.java_path = "java"      # exposed to the caller after success

    def cancel(self) -> None:
        """Request cancellation; checked between steps and output lines."""
        self._cancelled = True

    # ------------------------------------------------------------------ helpers
    def _emit(self, level: str, message: str) -> None:
        self.log.emit(level, message)

    def _check_cancel(self) -> None:
        if self._cancelled:
            raise RuntimeError("cancelled")

    def _run_java_streaming(self, args: list[str], cwd: str, timeout: int = 1800,
                            java: Optional[str] = None, stop_on_ready: bool = False) -> int:
        """
        Run a ``java`` command, streaming each output line to the log.

        When ``stop_on_ready`` is set, the moment the server reports that it has
        finished starting (``Done (…)!``) a ``stop`` command is written to its
        standard input so it shuts down cleanly and promptly. This is essential
        for the file-generation runs: otherwise the server keeps running and
        holds port 25565, causing an "Address already in use" error when the
        real server is started afterwards.

        Returns the process exit code. Honours cancellation and a wall-clock
        timeout (checked as output arrives).
        """
        executable = java or self._java
        proc = subprocess.Popen(
            [executable] + args,
            cwd=cwd,
            stdin=subprocess.PIPE if stop_on_ready else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
            creationflags=_NO_WINDOW,
        )
        start = time.time()
        sent_stop = False
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                self._emit(INFO, line)
            if stop_on_ready and not sent_stop and _DONE_RE.search(line):
                self._send_stdin(proc, "stop")
                sent_stop = True
            if self._cancelled:
                self._send_stdin(proc, "stop")
                if not self._wait_for_exit(proc, 8):
                    proc.kill()
                break
            if time.time() - start > timeout:
                self._emit(WARNING, f"Step timed out after {timeout}s; terminating.")
                self._send_stdin(proc, "stop")
                if not self._wait_for_exit(proc, 10):
                    proc.kill()
                break
        proc.wait()
        return proc.returncode if proc.returncode is not None else -1

    @staticmethod
    def _send_stdin(proc: subprocess.Popen, command: str) -> None:
        """Best-effort write of a command line to a process's standard input."""
        try:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.write(command + "\n")
                proc.stdin.flush()
        except (OSError, ValueError):
            pass

    @staticmethod
    def _wait_for_exit(proc: subprocess.Popen, seconds: int) -> bool:
        """Wait up to ``seconds`` for the process to exit; return True if it did."""
        try:
            proc.wait(timeout=seconds)
            return True
        except subprocess.TimeoutExpired:
            return False

    # ----------------------------------------------------------------- pipeline
    def run(self) -> None:  # noqa: D401 (QThread entry point)
        """Execute the installation pipeline."""
        path = self._session.install_path
        try:
            self._create_directory(path)
            self._check_cancel()

            self._ensure_java()
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
            self.busy.emit(False)

            self.java_path = self._java
            self._emit(SUCCESS, "log_done")
            self.finished_install.emit(True, server_jar)
        except RuntimeError as exc:
            self.busy.emit(False)
            if str(exc) == "cancelled":
                self.finished_install.emit(False, "cancelled")
            else:
                self._emit(ERROR, str(exc))
                self.finished_install.emit(False, str(exc))
        except Exception as exc:  # noqa: BLE001 — surfaced to the user
            self.busy.emit(False)
            self._emit(ERROR, str(exc))
            self.finished_install.emit(False, str(exc))

    # --------------------------------------------------------------- steps
    def _create_directory(self, path: str) -> None:
        self._emit(INFO, f"::log_creating_dir::{path}")
        os.makedirs(path, exist_ok=True)

    def _ensure_java(self) -> None:
        """Detect Java; download Eclipse Temurin automatically if necessary."""
        required = self._session.required_java
        resolved = java_manager.resolve_java(required)
        if resolved is not None:
            self._java = resolved
            where = "system" if resolved == "java" else "bundled"
            self._emit(SUCCESS, f"::log_java_ok::{required}")
            self._emit(INFO, f"Using {where} Java for the server.")
            return

        self._emit(WARNING, f"::log_java_missing::{required}")
        self.busy.emit(True)
        self._emit(INFO, f"::log_java_installing::{required}")
        self.busy.emit(False)
        self._java = java_manager.install_java(
            required,
            progress_callback=lambda d, t: self.progress.emit(d, t),
            log_callback=lambda msg: self._emit(INFO, msg),
        )
        self._emit(SUCCESS, f"::log_java_ready::{required}")

    def _resolve(self, path: str) -> ResolvedDownload:
        resolved = self._version_manager.resolve_download(
            self._session.platform, self._session.mc_version
        )
        if resolved.note:
            self._emit(INFO, resolved.note)
        return resolved

    def _download(self, resolved: ResolvedDownload, path: str) -> str:
        self._emit(INFO, f"::log_downloading::{resolved.filename}")
        self.busy.emit(False)
        dest = os.path.join(path, resolved.filename)
        downloader.download_file(
            resolved.url,
            dest,
            progress_callback=lambda d, t: self.progress.emit(d, t),
        )
        self._emit(SUCCESS, f"::log_downloaded::{resolved.filename}")
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
        """Turn an installer artifact into a runnable ``server.jar`` if needed."""
        if not resolved.is_installer:
            return jar_name

        self.busy.emit(True)
        if jar_name == "BuildTools.jar":
            result = self._build_with_buildtools(path)
            self.busy.emit(False)
            return result

        # Forge / NeoForge installer: run it, then remove the installer + logs.
        self._emit(INFO, "::log_running_installer::")
        code = self._run_java_streaming([f"-jar", jar_name, "--installServer"], cwd=path, timeout=1800)
        if code != 0:
            raise RuntimeError("The platform installer reported an error.")
        run_jar = self._find_first(path, prefix=self._session.platform, suffix=".jar")
        for junk in (jar_name, jar_name + ".log", "installer.log"):
            self._safe_remove(os.path.join(path, junk))
        self.busy.emit(False)
        return run_jar or jar_name

    def _build_with_buildtools(self, path: str) -> str:
        """
        Compile Spigot/CraftBukkit with BuildTools inside a temporary build
        directory, place only the final jar as ``server.jar`` and delete every
        intermediate artifact.
        """
        target = "spigot" if self._session.platform == "spigot" else "craftbukkit"
        build_dir = os.path.join(path, ".build")
        os.makedirs(build_dir, exist_ok=True)
        # BuildTools.jar was downloaded into ``path``; move it into the build dir.
        shutil.move(os.path.join(path, "BuildTools.jar"), os.path.join(build_dir, "BuildTools.jar"))

        self._emit(INFO, f"::log_building::{target}")
        code = self._run_java_streaming(
            ["-jar", "BuildTools.jar", "--rev", self._session.mc_version,
             "--compile", target, "--output-dir", path],
            cwd=build_dir,
            timeout=3600,
        )
        if code != 0:
            raise RuntimeError("BuildTools failed to compile the server.")

        produced = self._find_first(path, prefix=target, suffix=".jar")
        if not produced:
            raise RuntimeError("BuildTools did not produce a server jar.")
        final = os.path.join(path, "server.jar")
        self._safe_remove(final)
        shutil.move(os.path.join(path, produced), final)

        # Remove every build artifact, leaving a clean server directory.
        self._emit(INFO, "::log_cleanup::")
        shutil.rmtree(build_dir, ignore_errors=True)
        for junk in _BUILDTOOLS_JUNK:
            self._safe_remove(os.path.join(path, junk))
        return "server.jar"

    def _first_run(self, server_jar: str, path: str) -> None:
        self._emit(INFO, "log_running_first")
        self.busy.emit(True)
        # The first run normally exits on its own because the EULA has not been
        # accepted; stop_on_ready is a safety net for builds that start anyway.
        self._run_java_streaming(
            [f"-Xmx{self._session.xmx_mb}M", "-jar", server_jar, "nogui"],
            cwd=path,
            timeout=300,
            stop_on_ready=True,
        )
        self.busy.emit(False)

    def _accept_eula(self, path: str) -> None:
        self._emit(INFO, "log_eula")
        if not server_configurator.accept_eula(path):
            raise RuntimeError("Failed to write eula.txt")

    def _generate_properties(self, server_jar: str, path: str) -> None:
        if os.path.exists(os.path.join(path, "server.properties")):
            return
        self._emit(INFO, "log_configuring")
        self.busy.emit(True)
        # This run fully starts the server to generate server.properties and the
        # initial world, then stops it the moment it is ready so the port is
        # released before the real server is started.
        self._run_java_streaming(
            [f"-Xmx{self._session.xmx_mb}M", "-jar", server_jar, "nogui"],
            cwd=path,
            timeout=420,
            stop_on_ready=True,
        )
        self.busy.emit(False)

    def _apply_properties(self, path: str) -> None:
        self._emit(INFO, "log_editing")
        if not server_configurator.apply_server_properties(path, self._session, self._language):
            raise RuntimeError("Failed to write server.properties")
        self._emit(INFO, "log_motd")

    def _write_scripts(self, path: str, server_jar: str) -> None:
        if not self._session.generate_start_script:
            return
        self._emit(INFO, "log_scripts")
        server_configurator.write_start_scripts(path, self._session, server_jar, self._java)

    # ----------------------------------------------------------------- utils
    @staticmethod
    def _find_first(path: str, prefix: str, suffix: str) -> Optional[str]:
        for name in sorted(os.listdir(path)):
            lower = name.lower()
            if lower.startswith(prefix.lower()) and lower.endswith(suffix.lower()):
                return name
        return None

    @staticmethod
    def _safe_remove(target: str) -> None:
        try:
            if os.path.isdir(target):
                shutil.rmtree(target, ignore_errors=True)
            elif os.path.exists(target):
                os.remove(target)
        except OSError:
            pass
