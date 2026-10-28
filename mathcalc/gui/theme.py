"""Светлая и тёмная темы интерфейса (стиль Fusion + палитра + немного QSS)."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from ..plotting import DARK, LIGHT, PlotTheme

ACCENT = "#3B82F6"

_DARK_COLORS = {
    QPalette.Window: "#1E2030", QPalette.WindowText: "#E2E8F0", QPalette.Base: "#161724",
    QPalette.AlternateBase: "#24283B", QPalette.ToolTipBase: "#24283B", QPalette.ToolTipText: "#E2E8F0",
    QPalette.Text: "#E2E8F0", QPalette.Button: "#2A2E45", QPalette.ButtonText: "#E2E8F0",
    QPalette.BrightText: "#FFFFFF", QPalette.Highlight: ACCENT, QPalette.HighlightedText: "#FFFFFF",
    QPalette.PlaceholderText: "#64748B", QPalette.Link: "#60A5FA",
}
_LIGHT_COLORS = {
    QPalette.Window: "#F1F5F9", QPalette.WindowText: "#0F172A", QPalette.Base: "#FFFFFF",
    QPalette.AlternateBase: "#F8FAFC", QPalette.ToolTipBase: "#FFFFFF", QPalette.ToolTipText: "#0F172A",
    QPalette.Text: "#0F172A", QPalette.Button: "#E2E8F0", QPalette.ButtonText: "#0F172A",
    QPalette.BrightText: "#000000", QPalette.Highlight: ACCENT, QPalette.HighlightedText: "#FFFFFF",
    QPalette.PlaceholderText: "#94A3B8", QPalette.Link: "#2563EB",
}

_QSS = """
QTreeWidget { font-size: 10.5pt; border: none; }
QTreeWidget::item { padding: 3px 2px; }
QPushButton#primary { background-color: #10B981; color: white; font-weight: bold; padding: 7px 14px; border-radius: 6px; }
QPushButton#primary:hover { background-color: #059669; }
QLabel#taskTitle { font-size: 15pt; font-weight: bold; }
QLabel#groupLabel { font-weight: bold; margin-top: 6px; }
QLabel#error { color: #EF4444; font-weight: bold; }
QLabel#hint { color: #94A3B8; }
"""


def apply_theme(app: QApplication, dark: bool) -> PlotTheme:
    """Применяет тему ко всему приложению и возвращает соответствующую тему графиков."""
    app.setStyle("Fusion")
    pal = QPalette()
    for role, color in (_DARK_COLORS if dark else _LIGHT_COLORS).items():
        pal.setColor(role, QColor(color))
    disabled = QColor("#64748B" if dark else "#94A3B8")
    for role in (QPalette.Text, QPalette.ButtonText, QPalette.WindowText):
        pal.setColor(QPalette.Disabled, role, disabled)
    app.setPalette(pal)
    app.setStyleSheet(_QSS)
    return DARK if dark else LIGHT
