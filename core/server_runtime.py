"""
Server process management.

:class:`ServerRuntime` wraps a :class:`QProcess` that runs the Minecraft server
in-process (no external console window). It streams the server's console output,
forwards typed commands to the server's standard input, tracks the online player
count and reports live resource usage. A single instance manages one server.
"""

from __future__ import annotations

import os
import re
import time
from typing import Dict, List, Optional

import psutil
from PyQt6.QtCore import QProcess, QTimer, pyqtSignal, QObject

from core.server_configurator import jvm_flags
from core.server_registry import ServerRecord

# Matches Vanilla/Paper "There are 2 of a max of 20 players online:".
_LIST_RE = re.compile(r"There are (\d+)\s*(?:of a max(?: of)?|/)\s*(\d+)", re.IGNORECASE)
# Server finished starting.
_DONE_RE = re.compile(r'Done \([\d.]+s\)!')


class ServerRuntime(QObject):
    """Controls and monitors a single server process."""

    output = pyqtSignal(str)                 # a chunk of console text
    state_changed = pyqtSignal(bool)         # True = running, False = stopped
    players_changed = pyqtSignal(int, int)   # online, maximum
    stats_changed = pyqtSignal(float, float) # cpu percent, memory MB
    ready = pyqtSignal()                     # server finished starting

    def __init__(self, record: ServerRecord, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._record = record
        self._process: Optional[QProcess] = None
        self._started_at = 0.0
        self._online = 0
        self._max_players = 0
        self._psutil_proc: Optional[psutil.Process] = None
        self._restart_after_stop = False
        self._restart_delay_ms = 3000
        # Rolling console buffer so the text survives navigating away and back.
        self._buffer: str = ""
        self._buffer_limit = 200_000

        # Periodic poll for player count and resource stats.
        self._poll = QTimer(self)
        self._poll.setInterval(5000)
        self._poll.timeout.connect(self._poll_tick)

    # ------------------------------------------------------------------ state
    @property
    def record(self) -> ServerRecord:
        return self._record

    def is_running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def uptime_seconds(self) -> int:
        if not self.is_running() or not self._started_at:
            return 0
        return int(time.time() - self._started_at)

    @property
    def online_players(self) -> int:
        return self._online

    @property
    def max_players(self) -> int:
        return self._max_players

    def console_text(self) -> str:
        """Return the accumulated console output."""
        return self._buffer

    def _append_buffer(self, text: str) -> None:
        self._buffer += text
        if len(self._buffer) > self._buffer_limit:
            self._buffer = self._buffer[-self._buffer_limit:]

    # ------------------------------------------------------------------ start
    def start(self) -> bool:
        """
        Start the server. Returns ``False`` if it is already running or the jar
        is missing.
        """
        if self.is_running():
            return False
        jar_path = os.path.join(self._record.path, self._record.jar)
        if not os.path.isfile(jar_path):
            self.output.emit(f"[ServerCreator] Server jar not found: {jar_path}\n")
            return False

        flags = jvm_flags(self._record) if self._record.use_aikar_flags else ""
        args = [f"-Xms{self._record.xms_mb}M", f"-Xmx{self._record.xmx_mb}M"]
        args += [a for a in flags.split(" ") if a]
        args += ["-jar", self._record.jar, "nogui"]

        self._process = QProcess(self)
        self._process.setWorkingDirectory(self._record.path)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.started.connect(self._on_started)
        self._process.finished.connect(self._on_finished)
        java = getattr(self._record, "java_path", "java") or "java"
        self._process.start(java, args)
        return True

    # ------------------------------------------------------------------- stop
    def stop(self, force_after_ms: int = 12000) -> None:
        """
        Gracefully stop the server by sending the ``stop`` command, then force
        terminate if it does not exit within ``force_after_ms``.
        """
        proc = self._process
        if not self.is_running() or proc is None:
            return
        self.send_command("stop")

        # Capture this exact process so a later restart's new process is never
        # killed by a stale timer.
        def _kill() -> None:
            if proc.state() != QProcess.ProcessState.NotRunning:
                proc.kill()

        QTimer.singleShot(force_after_ms, _kill)

    def restart(self) -> None:
        """
        Restart the server: stop it, then start again a few seconds after it has
        fully shut down. The delay lets the operating system release file locks
        (such as ``logs/latest.log``) before the new instance starts.
        """
        if self.is_running():
            self._restart_after_stop = True
            self.stop()
        else:
            self.start()

    # --------------------------------------------------------------- commands
    def send_command(self, command: str) -> None:
        """Write ``command`` to the server's standard input (adds a newline)."""
        if not self.is_running() or self._process is None:
            return
        self._process.write((command.rstrip("\n") + "\n").encode("utf-8", "replace"))

    # ---------------------------------------------------------------- signals
    def _on_started(self) -> None:
        self._started_at = time.time()
        try:
            self._psutil_proc = psutil.Process(int(self._process.processId()))
            self._psutil_proc.cpu_percent(None)  # prime the measurement
        except (psutil.Error, ValueError):
            self._psutil_proc = None
        self._poll.start()
        self.state_changed.emit(True)

    def _on_finished(self, _code, _status) -> None:
        self._poll.stop()
        self._started_at = 0.0
        self._online = 0
        self._psutil_proc = None
        # Release the finished process so its file handles are freed and a fresh
        # QProcess is used on the next start.
        finished = self._process
        self._process = None
        if finished is not None:
            finished.deleteLater()
        self.players_changed.emit(0, 0)
        self.state_changed.emit(False)
        if self._restart_after_stop:
            self._restart_after_stop = False
            self.output.emit("\n[ServerCreator] Restarting in 3 seconds…\n")
            QTimer.singleShot(self._restart_delay_ms, self.start)

    def _read_output(self) -> None:
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardOutput()).decode("utf-8", "replace")
        if not data:
            return
        self._append_buffer(data)
        self.output.emit(data)
        if _DONE_RE.search(data):
            self.ready.emit()
        match = _LIST_RE.search(data)
        if match:
            self._online = int(match.group(1))
            self._max_players = int(match.group(2))
            self.players_changed.emit(self._online, self._max_players)

    def _poll_tick(self) -> None:
        # Ask the server for its player list; the reply is parsed in _read_output.
        self.send_command("list")
        if self._psutil_proc is not None:
            try:
                cpu = self._psutil_proc.cpu_percent(None)
                mem = self._psutil_proc.memory_info().rss / (1024 * 1024)
                # Include child JVM if the launcher forked one.
                for child in self._psutil_proc.children(recursive=True):
                    try:
                        mem += child.memory_info().rss / (1024 * 1024)
                    except psutil.Error:
                        pass
                self.stats_changed.emit(cpu, mem)
            except psutil.Error:
                pass


class RuntimeManager(QObject):
    """
    Owns the live :class:`ServerRuntime` instances keyed by server path.

    Keeping runtimes here (rather than inside a view) means a server keeps
    running while the user navigates between the list and other pages.
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._runtimes: Dict[str, ServerRuntime] = {}

    def get(self, record: ServerRecord) -> ServerRuntime:
        """Return the runtime for ``record``, creating it on first access."""
        key = os.path.normcase(record.path)
        runtime = self._runtimes.get(key)
        if runtime is None:
            runtime = ServerRuntime(record, self)
            self._runtimes[key] = runtime
        return runtime

    def discard(self, path: str) -> None:
        """Forget the runtime for a (deleted) server path."""
        self._runtimes.pop(os.path.normcase(path), None)

    def running(self) -> List[ServerRuntime]:
        """Return every runtime that is currently running."""
        return [r for r in self._runtimes.values() if r.is_running()]

    def stop_all(self) -> None:
        """Force-stop every running server (used on application quit)."""
        for runtime in self._runtimes.values():
            if runtime.is_running():
                runtime.stop(force_after_ms=800)
