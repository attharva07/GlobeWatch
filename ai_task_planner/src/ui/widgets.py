"""Reusable UI widgets."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

class PriorityChip(QLabel):
    """Colored label representing task priority."""

    COLORS = {
        "low": QColor(85, 170, 85),
        "medium": QColor(66, 133, 244),
        "high": QColor(219, 68, 55),
        "urgent": QColor(244, 160, 0),
    }

    def __init__(self, priority: str, parent: QWidget | None = None) -> None:
        super().__init__(priority.capitalize(), parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMargin(4)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.set_priority(priority)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet("border-radius: 8px; padding: 2px 6px; color: #111;")

    def set_priority(self, priority: str) -> None:
        color = self.COLORS.get(priority, QColor(120, 120, 120))
        self.setText(priority.capitalize())
        self.setStyleSheet(
            f"border-radius: 8px; padding: 2px 6px; color: #111; background-color: {color.name()};"
        )


class TaskRow(QWidget):
    """Widget summarizing a task in the list view."""

    def __init__(self, task, on_select: Callable[[int], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.task = task
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        self.priority_chip = PriorityChip(task.priority)
        title_label = QLabel(task.title)
        title_label.setWordWrap(True)
        status_label = QLabel(task.status.replace("_", " ").title())
        status_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.priority_chip)
        layout.addWidget(title_label, 1)
        layout.addWidget(status_label)
        button = QPushButton("Open")
        button.clicked.connect(lambda: on_select(task.id))
        layout.addWidget(button)

    def update_task(self, task) -> None:
        self.task = task
        self.priority_chip.set_priority(task.priority)
