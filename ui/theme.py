"""
Application theming.

Two fully self-consistent palettes are provided — ``dark`` and ``light``. Both
explicitly define foreground and background colours for *every* styled widget
type, so there are no contrast defects such as dark text on a dark background or
white popup lists in dark mode. Theme can be switched freely at runtime; the
selected language, by contrast, is fixed for the lifetime of the installation.
"""

from __future__ import annotations

from typing import Dict

# Shared accent / status colours (brand consistent across both themes).
ACCENT = "#3FB950"
ACCENT_HOVER = "#46C95A"
ACCENT_PRESSED = "#359343"
ERROR = "#F85149"
WARNING = "#D29922"
SUCCESS = "#3FB950"

DARK: Dict[str, str] = {
    "bg": "#0D1117",
    "panel": "#161B22",
    "panel_alt": "#1C2128",
    "border": "#30363D",
    "text": "#E6EDF3",
    "text_secondary": "#8B949E",
    "input_bg": "#0D1117",
    "input_disabled_bg": "#161B22",
    "selection_bg": "#1F6FEB",
    "selection_text": "#FFFFFF",
    "log_bg": "#010409",
}

LIGHT: Dict[str, str] = {
    "bg": "#F6F8FA",
    "panel": "#FFFFFF",
    "panel_alt": "#F0F2F5",
    "border": "#D0D7DE",
    "text": "#1F2328",
    "text_secondary": "#57606A",
    "input_bg": "#FFFFFF",
    "input_disabled_bg": "#EAEEF2",
    "selection_bg": "#0969DA",
    "selection_text": "#FFFFFF",
    "log_bg": "#0D1117",  # log stays dark for readability in both themes
}

THEMES = {"dark": DARK, "light": LIGHT}
DEFAULT_THEME = "dark"


def status_color(level: str) -> str:
    """Map a log level (INFO/WARNING/ERROR/SUCCESS) to a display colour."""
    return {
        "INFO": "#C9D1D9",
        "WARNING": WARNING,
        "ERROR": ERROR,
        "SUCCESS": SUCCESS,
    }.get(level, "#C9D1D9")


def build_stylesheet(theme_name: str) -> str:
    """Return a complete Qt stylesheet string for the named theme."""
    c = THEMES.get(theme_name, DARK)
    return f"""
    QWidget {{
        background-color: {c['bg']};
        color: {c['text']};
        font-family: "Segoe UI", "Arial";
        font-size: 14px;
    }}
    QMainWindow, QDialog {{ background-color: {c['bg']}; }}

    /* Panels / cards */
    QFrame#Card, QFrame#Panel {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 8px;
    }}
    QFrame#TopBar {{
        background-color: {c['panel']};
        border-bottom: 1px solid {c['border']};
    }}
    QFrame#SideBar {{
        background-color: {c['panel_alt']};
        border-right: 1px solid {c['border']};
    }}
    QFrame#Divider {{ background-color: {c['border']}; border: none; }}

    QLabel {{ background: transparent; color: {c['text']}; }}
    QLabel#Title {{ font-size: 22px; font-weight: 600; color: {c['text']}; }}
    QLabel#Subtitle {{ font-size: 14px; color: {c['text_secondary']}; }}
    QLabel#Secondary {{ color: {c['text_secondary']}; }}
    QLabel#Accent {{ color: {ACCENT}; }}
    QLabel#Error {{ color: {ERROR}; }}
    QLabel#Warning {{ color: {WARNING}; }}
    QLabel#StepActive {{ color: {ACCENT}; font-weight: 600; }}
    QLabel#StepDone {{ color: {c['text']}; }}
    QLabel#StepPending {{ color: {c['text_secondary']}; }}

    /* Buttons */
    QPushButton {{
        background-color: {c['panel_alt']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 8px 18px;
    }}
    QPushButton:hover {{ border-color: {ACCENT}; }}
    QPushButton:disabled {{ color: {c['text_secondary']}; background-color: {c['input_disabled_bg']}; }}
    QPushButton#Primary {{
        background-color: {ACCENT};
        color: #04240C;
        font-weight: 600;
        border: 1px solid {ACCENT};
    }}
    QPushButton#Primary:hover {{ background-color: {ACCENT_HOVER}; }}
    QPushButton#Primary:pressed {{ background-color: {ACCENT_PRESSED}; }}
    QPushButton#Primary:disabled {{
        background-color: {c['input_disabled_bg']};
        color: {c['text_secondary']};
        border-color: {c['border']};
    }}
    QPushButton#Link {{
        background: transparent; border: none; color: {ACCENT}; text-decoration: underline;
        padding: 2px;
    }}

    /* Platform selection cards */
    QPushButton#PlatformCard {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 14px;
        text-align: left;
    }}
    QPushButton#PlatformCard:hover {{ border-color: {ACCENT}; background-color: {c['panel_alt']}; }}
    QPushButton#PlatformCard:checked {{ border: 2px solid {ACCENT}; background-color: {c['panel_alt']}; }}

    /* Text inputs */
    QLineEdit, QSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
        background-color: {c['input_bg']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 6px 8px;
        selection-background-color: {c['selection_bg']};
        selection-color: {c['selection_text']};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
    QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
        background-color: {c['input_disabled_bg']};
        color: {c['text_secondary']};
    }}
    QLineEdit#Valid {{ border: 1px solid {ACCENT}; }}
    QLineEdit#Invalid {{ border: 1px solid {ERROR}; }}

    /* ComboBox popup — explicitly themed to avoid a white list in dark mode */
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background-color: {c['panel']};
        color: {c['text']};
        border: 1px solid {c['border']};
        selection-background-color: {c['selection_bg']};
        selection-color: {c['selection_text']};
        outline: none;
    }}

    /* SpinBox buttons */
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {c['panel_alt']};
        border-left: 1px solid {c['border']};
        width: 18px;
    }}

    /* Checkboxes / radios */
    QCheckBox, QRadioButton {{ background: transparent; color: {c['text']}; spacing: 8px; }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px; height: 18px;
        border: 1px solid {c['border']};
        background-color: {c['input_bg']};
        border-radius: 4px;
    }}
    QRadioButton::indicator {{ border-radius: 9px; }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        height: 6px; background: {c['border']}; border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
    QSlider::handle:horizontal {{
        background: {c['text']}; width: 16px; margin: -6px 0; border-radius: 8px;
    }}

    /* Progress bar */
    QProgressBar {{
        background-color: {c['panel_alt']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        text-align: center;
        color: {c['text']};
        height: 22px;
    }}
    QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 3px; }}

    /* Log viewer */
    QPlainTextEdit#LogViewer {{
        background-color: {c['log_bg']};
        color: #C9D1D9;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 13px;
        border: 1px solid {c['border']};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{ background: {c['bg']}; width: 12px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 6px; min-height: 24px; }}
    QScrollBar::handle:vertical:hover {{ background: {c['text_secondary']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollArea {{ border: none; background: transparent; }}

    /* Tooltips */
    QToolTip {{
        background-color: {c['panel']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 4px;
    }}

    /* Message boxes */
    QMessageBox {{ background-color: {c['panel']}; }}
    QMessageBox QLabel {{ color: {c['text']}; }}
    """
