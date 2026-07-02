"""Centralized color palette, fonts, and QSS stylesheet for the app."""

BG = "#0F1117"
PANEL = "#161B22"
PANEL_ALT = "#1B212B"
ACCENT = "#4F8CFF"
SUCCESS = "#3FB950"
WARNING = "#F2C94C"
DANGER = "#F85149"
TEXT = "#FFFFFF"
TEXT_SECONDARY = "#9DA5B4"
BORDER = "#242B38"

FONT_FAMILY = "Segoe UI"


def stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: '{FONT_FAMILY}';
        font-size: 13px;
    }}
    QFrame#panel {{
        background-color: {PANEL};
        border-radius: 14px;
        border: 1px solid {BORDER};
    }}
    QFrame#topBar {{
        background-color: {PANEL};
        border-bottom: 1px solid {BORDER};
    }}
    QFrame#statusBar {{
        background-color: {PANEL};
        border-top: 1px solid {BORDER};
    }}
    QLabel#title {{
        font-size: 15px;
        font-weight: 600;
        color: {TEXT};
    }}
    QLabel#secondary {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
    }}
    QLabel#sectionHeader {{
        color: {TEXT_SECONDARY};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
    }}
    QScrollArea, QScrollArea > QWidget > QWidget {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QPushButton {{
        background-color: {PANEL_ALT};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{
        background-color: #222938;
        border: 1px solid {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: #1a2029;
    }}
    QPushButton#primary {{
        background-color: {ACCENT};
        border: none;
        color: white;
        font-weight: 600;
    }}
    QPushButton#primary:hover {{
        background-color: #6a9cff;
    }}
    QPushButton#iconBtn {{
        background-color: transparent;
        border: none;
        border-radius: 18px;
        padding: 6px;
    }}
    QPushButton#iconBtn:hover {{
        background-color: {PANEL_ALT};
    }}
    QLineEdit#commandInput {{
        background-color: {PANEL_ALT};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 12px 16px;
        font-size: 14px;
        color: {TEXT};
    }}
    QLineEdit#commandInput:focus {{
        border: 1px solid {ACCENT};
    }}
    """
