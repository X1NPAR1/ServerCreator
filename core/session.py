"""
Central session state shared between every wizard step.

A single :class:`ServerSession` instance is created by the main window and
injected into each step widget. Steps read and write their relevant fields,
which keeps the wizard's data flow explicit and easy to reason about.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ServerSession:
    """Holds every user choice collected throughout the wizard."""

    # Step 1 — platform
    platform: str = ""            # "vanilla", "paper", "fabric", ...

    # Step 2 — version
    mc_version: str = ""          # "1.21.1", "1.20.4", ...
    required_java: int = 8        # minimum Java major version for mc_version

    # Step 3 — name & location
    server_name: str = ""         # "MyServer"
    base_directory: str = ""      # r"C:\Servers"

    # Step 4 — performance
    xms_mb: int = 1024
    xmx_mb: int = 2048
    use_aikar_flags: bool = True
    generate_start_script: bool = True

    # Step 5 — configuration
    online_mode: bool = True
    max_players: int = 20
    gamemode: str = "survival"
    hardcore: bool = False
    whitelist: bool = False
    server_port: int = 25565
    pvp: bool = True
    allow_nether: bool = True
    level_seed: str = ""

    @property
    def install_path(self) -> str:
        """
        Return the fully resolved installation path.

        Derived dynamically from ``base_directory`` and ``server_name`` so it
        always stays consistent regardless of the order in which the user edits
        those fields.
        """
        if not self.base_directory or not self.server_name:
            return ""
        return os.path.join(self.base_directory, self.server_name.strip())

    def reset(self) -> None:
        """Restore every field to its default value (used by 'Create Another')."""
        defaults = ServerSession()
        for field_name in vars(defaults):
            setattr(self, field_name, getattr(defaults, field_name))
