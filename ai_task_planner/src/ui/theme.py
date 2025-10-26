"""UI theming helpers."""

from __future__ import annotations

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


PRIMARY_BG = QColor(30, 30, 30)
PRIMARY_TEXT = QColor(235, 235, 235)
ACCENT = QColor(0, 122, 204)
SECONDARY_BG = QColor(45, 45, 45)
MUTED_TEXT = QColor(180, 180, 180)


def apply_dark_theme(app: QApplication) -> None:
    """Apply the global dark palette to the QApplication."""

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, PRIMARY_BG)
    palette.setColor(QPalette.ColorRole.WindowText, PRIMARY_TEXT)
    palette.setColor(QPalette.ColorRole.Base, SECONDARY_BG)
    palette.setColor(QPalette.ColorRole.AlternateBase, PRIMARY_BG)
    palette.setColor(QPalette.ColorRole.ToolTipBase, PRIMARY_TEXT)
    palette.setColor(QPalette.ColorRole.ToolTipText, PRIMARY_TEXT)
    palette.setColor(QPalette.ColorRole.Text, PRIMARY_TEXT)
    palette.setColor(QPalette.ColorRole.Button, SECONDARY_BG)
    palette.setColor(QPalette.ColorRole.ButtonText, PRIMARY_TEXT)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, ACCENT)
    palette.setColor(QPalette.ColorRole.HighlightedText, PRIMARY_TEXT)
    palette.setColor(QPalette.ColorRole.PlaceholderText, MUTED_TEXT)
    app.setPalette(palette)
