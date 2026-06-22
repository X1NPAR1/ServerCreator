"""
Persistent user preferences (language, theme, last used directory).

The configuration lives in ``%APPDATA%\\ServerCreator\\config.json``. The
language, once chosen on first launch, is treated as immutable by the rest of
the application.
"""

from __future__ import annotations

from translations import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from utils import config_path, read_json, write_json

# Theme identifiers (kept here to avoid a core -> ui import dependency).
VALID_THEMES = ("dark", "light")
DEFAULT_THEME = "dark"


class AppConfig:
    """Loads, exposes and persists the user's preferences."""

    def __init__(self) -> None:
        self._data = read_json(config_path(), default={}) or {}

    # -- language (write-once) --------------------------------------------- #
    @property
    def language(self):
        lang = self._data.get("language")
        return lang if lang in SUPPORTED_LANGUAGES else None

    def is_language_set(self) -> bool:
        return self.language is not None

    def set_language(self, language: str) -> None:
        """Persist the chosen language. Intended to be called only once."""
        if language not in SUPPORTED_LANGUAGES:
            language = DEFAULT_LANGUAGE
        self._data["language"] = language
        self.save()

    # -- theme (mutable) ---------------------------------------------------- #
    @property
    def theme(self) -> str:
        theme = self._data.get("theme", DEFAULT_THEME)
        return theme if theme in VALID_THEMES else DEFAULT_THEME

    def set_theme(self, theme: str) -> None:
        if theme in VALID_THEMES:
            self._data["theme"] = theme
            self.save()

    # -- last directory ----------------------------------------------------- #
    @property
    def last_directory(self) -> str:
        return self._data.get("last_directory", "")

    def set_last_directory(self, directory: str) -> None:
        self._data["last_directory"] = directory
        self.save()

    def save(self) -> None:
        write_json(config_path(), self._data)
