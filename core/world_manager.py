"""
World and server file management: list/create/backup worlds and delete servers.
"""

from __future__ import annotations

import os
import shutil
import time
import zipfile
from typing import List

from core.server_configurator import read_properties, write_properties


def current_level_name(server_path: str) -> str:
    """Return the configured ``level-name`` (defaults to ``world``)."""
    props = read_properties(server_path)
    return props.get("level-name", "world") or "world"


def list_worlds(server_path: str) -> List[str]:
    """
    Return the names of world folders in the server directory.

    A folder is considered a world if it contains a ``level.dat`` file. The
    associated dimension folders (``*_nether`` / ``*_the_end``) are not listed
    separately.
    """
    worlds: List[str] = []
    if not os.path.isdir(server_path):
        return worlds
    for name in sorted(os.listdir(server_path)):
        full = os.path.join(server_path, name)
        if name.endswith(("_nether", "_the_end")):
            continue
        if os.path.isdir(full) and os.path.isfile(os.path.join(full, "level.dat")):
            worlds.append(name)
    return worlds


def create_world(server_path: str, new_name: str) -> None:
    """
    Switch the server to a brand new world.

    The new ``level-name`` is written to ``server.properties``; Minecraft
    generates the world on the next start. The previous world folders are left
    intact so they can be restored by switching the name back.

    Raises:
        ValueError: if ``new_name`` is empty or already in use as a world.
    """
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("World name cannot be empty.")
    if os.path.exists(os.path.join(server_path, new_name)):
        raise ValueError("A world with this name already exists.")
    write_properties(server_path, {"level-name": new_name})


def backup_world(server_path: str, world_name: str, destination_dir: str) -> str:
    """
    Create a timestamped ``.zip`` backup of ``world_name`` (and its Nether/End
    dimensions if present) inside ``destination_dir``.

    Returns:
        The path to the created archive.

    Raises:
        FileNotFoundError: if the world folder does not exist.
    """
    world_path = os.path.join(server_path, world_name)
    if not os.path.isdir(world_path):
        raise FileNotFoundError(world_name)
    os.makedirs(destination_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    archive = os.path.join(destination_dir, f"{world_name}-{stamp}.zip")

    folders = [world_name]
    for suffix in ("_nether", "_the_end"):
        if os.path.isdir(os.path.join(server_path, world_name + suffix)):
            folders.append(world_name + suffix)

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in folders:
            base = os.path.join(server_path, folder)
            for root, _dirs, files in os.walk(base):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, server_path)
                    zf.write(abs_path, rel_path)
    return archive


def delete_server(server_path: str) -> None:
    """Permanently delete the entire server directory."""
    if os.path.isdir(server_path):
        shutil.rmtree(server_path, ignore_errors=True)
