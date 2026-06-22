"""
Persistent registry of installed servers.

Every server created by the wizard is recorded in ``servers.json`` inside the
per-user data directory so the "My Servers" view can list and manage them
across sessions. The registry stores only metadata; the actual server files
live wherever the user chose to install them.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from utils import app_data_dir, read_json, write_json


def _registry_path() -> str:
    return os.path.join(app_data_dir(), "servers.json")


@dataclass
class ServerRecord:
    """Metadata describing a single installed server."""

    name: str
    path: str
    platform: str = ""
    mc_version: str = ""
    port: int = 25565
    jar: str = "server.jar"
    xms_mb: int = 1024
    xmx_mb: int = 2048
    use_aikar_flags: bool = True
    created_at: float = field(default_factory=time.time)

    @property
    def exists(self) -> bool:
        """Return whether the server jar is still present on disk."""
        return os.path.isfile(os.path.join(self.path, self.jar))


class ServerRegistry:
    """Loads, mutates and persists the list of installed servers."""

    def __init__(self) -> None:
        self._records: List[ServerRecord] = []
        self._load()

    def _load(self) -> None:
        raw = read_json(_registry_path(), default=[]) or []
        self._records = []
        for item in raw:
            try:
                self._records.append(ServerRecord(**item))
            except TypeError:
                # Ignore entries written by an incompatible future version.
                continue

    def _save(self) -> None:
        write_json(_registry_path(), [asdict(r) for r in self._records])

    # ------------------------------------------------------------------ query
    def all(self) -> List[ServerRecord]:
        """Return all registered servers (newest first)."""
        return sorted(self._records, key=lambda r: r.created_at, reverse=True)

    def count(self) -> int:
        return len(self._records)

    def get(self, path: str) -> Optional[ServerRecord]:
        for record in self._records:
            if os.path.normcase(record.path) == os.path.normcase(path):
                return record
        return None

    # ----------------------------------------------------------------- mutate
    def add(self, record: ServerRecord) -> None:
        """Add or replace a server record keyed by its install path."""
        existing = self.get(record.path)
        if existing is not None:
            self._records.remove(existing)
        self._records.append(record)
        self._save()

    def remove(self, path: str) -> None:
        record = self.get(path)
        if record is not None:
            self._records.remove(record)
            self._save()

    def prune_missing(self) -> None:
        """Drop records whose files no longer exist on disk."""
        before = len(self._records)
        self._records = [r for r in self._records if os.path.isdir(r.path)]
        if len(self._records) != before:
            self._save()
