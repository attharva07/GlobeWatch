"""Main PyQt6 window for the AI Task Planner."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy import and_, or_, select

from ..core import ai_parser
from ..core.config import get_config
from ..core.db import session_scope
from ..core.models import Task
from ..core.scheduler import SchedulerManager
from ..core.sync import run_sync
from ..core.validators import ensure_priority, ensure_status
from .theme import apply_dark_theme
from .widgets import TaskRow

LOGGER = logging.getLogger(__name__)


class WorkerThread(QThread):
    """Run a callable in a background QThread."""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn: Callable, *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:  # noqa: D401
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Worker error", exc_info=exc)
            self.error.emit(str(exc))


class AiParseDialog(QDialog):
    """Dialog for AI-assisted task parsing."""

    parsed = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None, initial_text: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Parse Task")
        layout = QVBoxLayout(self)
        self.input_edit = QPlainTextEdit(initial_text)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        parse_button = QPushButton("Parse")
        parse_button.clicked.connect(self._trigger_parse)
        layout.addWidget(QLabel("Enter free-form task notes:"))
        layout.addWidget(self.input_edit)
        layout.addWidget(parse_button)
        layout.addWidget(QLabel("Parsed JSON preview:"))
        layout.addWidget(self.preview)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._last_payload: Optional[dict] = None
        self.thread: Optional[WorkerThread] = None

    def _trigger_parse(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Parse Error", "Enter some text to parse")
            return
        self.preview.setPlainText("Parsing...")
        self.thread = WorkerThread(ai_parser.parse_free_text, text)
        self.thread.finished.connect(self._on_parsed)
        self.thread.error.connect(self._on_error)
        self.thread.start()

    def _on_parsed(self, payload: object) -> None:
        self._last_payload = payload  # type: ignore[assignment]
        self.preview.setPlainText(json.dumps(payload, indent=2))
        self.parsed.emit(payload)  # type: ignore[arg-type]
        self.thread = None

    def _on_error(self, message: str) -> None:
        self.preview.setPlainText(f"Error: {message}")
        self.thread = None

    def get_payload(self) -> Optional[dict]:
        return self._last_payload


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, scheduler: SchedulerManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.scheduler = scheduler
        self.setWindowTitle("AI Task Planner")
        self.resize(1200, 720)
        self.config = get_config()
        self.current_task: Optional[Task] = None
        self.worker: Optional[WorkerThread] = None

        self._build_ui()
        self._load_tasks()

    def _build_ui(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.add_task_action = QAction("Add Task", self)
        self.add_task_action.setShortcut("Ctrl+N")
        self.add_task_action.triggered.connect(self._show_add_dialog)
        toolbar.addAction(self.add_task_action)

        self.ai_parse_action = QAction("AI Parse", self)
        self.ai_parse_action.triggered.connect(self._ai_parse_current)
        toolbar.addAction(self.ai_parse_action)

        self.mark_done_action = QAction("Mark Done", self)
        self.mark_done_action.triggered.connect(self._mark_done)
        toolbar.addAction(self.mark_done_action)

        self.sync_action = QAction("Sync", self)
        self.sync_action.setShortcut("F5")
        self.sync_action.triggered.connect(self._run_sync)
        toolbar.addAction(self.sync_action)

        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter tasks")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(lambda _: self._load_tasks())
        toolbar.addWidget(search_label)
        toolbar.addWidget(self.search_edit)
        self.search_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.search_edit.setMinimumWidth(200)

        central = QWidget()
        layout = QGridLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.calendar = self._create_calendar()
        layout.addWidget(self.calendar, 0, 0)

        self.task_list = QListWidget()
        self.task_list.itemSelectionChanged.connect(self._on_task_selected)
        layout.addWidget(self.task_list, 0, 1)

        self.detail_panel = self._build_detail_panel()
        layout.addWidget(self.detail_panel, 0, 2)

        central.setLayout(layout)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.setStatusBar(status)

    def _create_calendar(self) -> QWidget:
        from PyQt6.QtWidgets import QCalendarWidget

        calendar = QCalendarWidget()
        calendar.selectionChanged.connect(self._load_tasks)
        calendar.setGridVisible(True)
        calendar.setSelectedDate(QDate.currentDate())
        calendar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return calendar

    def _build_detail_panel(self) -> QWidget:
        panel = QWidget()
        layout = QFormLayout(panel)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Task title")
        self.title_edit.setClearButtonEnabled(True)
        self.description_edit = QTextEdit()
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["low", "medium", "high", "urgent"])
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pending", "in_progress", "done"])
        self.start_edit = QDateTimeEdit()
        self.start_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.start_edit.setCalendarPopup(True)
        self.due_edit = QDateTimeEdit()
        self.due_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_edit.setCalendarPopup(True)
        self.save_button = QPushButton("Save")
        self.save_button.setShortcut("Ctrl+S")
        self.save_button.clicked.connect(self._save_task)

        layout.addRow("Title", self.title_edit)
        layout.addRow("Description", self.description_edit)
        layout.addRow("Priority", self.priority_combo)
        layout.addRow("Status", self.status_combo)
        layout.addRow("Start", self.start_edit)
        layout.addRow("Due", self.due_edit)
        layout.addRow(self.save_button)
        return panel

    def _load_tasks(self) -> None:
        self.task_list.clear()
        selected_date = self.calendar.selectedDate()
        filter_text = self.search_edit.text().lower()
        selected_id = self.current_task.id if self.current_task else None
        start_local = datetime(
            selected_date.year(), selected_date.month(), selected_date.day(), tzinfo=self.config.timezone
        )
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)
        with session_scope() as session:
            stmt = select(Task).where(
                or_(
                    Task.due_ts.is_(None),
                    and_(Task.due_ts >= start_utc, Task.due_ts < end_utc),
                )
            )
            tasks = list(session.scalars(stmt))
        for task in tasks:
            searchable = f"{task.title} {task.description}".lower()
            if filter_text and filter_text not in searchable:
                continue
            item = QListWidgetItem()
            widget = TaskRow(task, self._select_task_by_id)
            item.setSizeHint(widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, widget)
            item.setData(Qt.ItemDataRole.UserRole, task.id)
        if selected_id:
            self._select_task_by_id(selected_id)

    def _select_task_by_id(self, task_id: int) -> None:
        for index in range(self.task_list.count()):
            item = self.task_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == task_id:
                self.task_list.setCurrentRow(index)
                break

    def _on_task_selected(self) -> None:
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            self.current_task = None
            self._clear_details()
            return
        task_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        with session_scope() as session:
            task = session.get(Task, task_id)
        self.current_task = task
        if not task:
            self._clear_details()
            return
        self._populate_details(task)

    def _clear_details(self) -> None:
        self.title_edit.clear()
        self.description_edit.clear()
        self.priority_combo.setCurrentIndex(1)
        self.status_combo.setCurrentIndex(0)
        now = datetime.now(self.config.timezone)
        self.start_edit.setDateTime(now)
        self.due_edit.setDateTime(now)

    def _populate_details(self, task: Task) -> None:
        self.title_edit.setText(task.title)
        self.description_edit.setPlainText(task.description)
        self.priority_combo.setCurrentText(task.priority)
        self.status_combo.setCurrentText(task.status)
        if task.start_ts:
            self.start_edit.setDateTime(task.start_ts.astimezone(self.config.timezone))
        if task.due_ts:
            self.due_edit.setDateTime(task.due_ts.astimezone(self.config.timezone))

    def _save_task(self) -> None:
        if not self.current_task:
            QMessageBox.information(self, "Save Task", "Select a task to save changes.")
            return
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation", "Title is required")
            return
        priority = ensure_priority(self.priority_combo.currentText())
        status = ensure_status(self.status_combo.currentText())
        start_dt = self.start_edit.dateTime().toPyDateTime().replace(tzinfo=self.config.timezone)
        due_dt = self.due_edit.dateTime().toPyDateTime().replace(tzinfo=self.config.timezone)
        with session_scope() as session:
            task = session.get(Task, self.current_task.id)
            if not task:
                return
            task.title = title
            task.description = self.description_edit.toPlainText().strip()
            task.priority = priority
            task.status = status
            task.start_ts = start_dt.astimezone(timezone.utc)
            task.due_ts = due_dt.astimezone(timezone.utc)
        self.statusBar().showMessage("Task saved", 2000)
        self._load_tasks()

    def _mark_done(self) -> None:
        if not self.current_task:
            return
        with session_scope() as session:
            task = session.get(Task, self.current_task.id)
            if task:
                task.status = "done"
        self.statusBar().showMessage("Task marked done", 2000)
        self._load_tasks()

    def _run_sync(self) -> None:
        self.statusBar().showMessage("Syncing...")
        self.worker = WorkerThread(run_sync)
        self.worker.finished.connect(lambda _: self._on_sync_complete())
        self.worker.error.connect(lambda msg: self._on_sync_error(msg))
        self.worker.start()

    def _on_sync_complete(self) -> None:
        self.statusBar().showMessage("Sync complete", 3000)
        self._load_tasks()
        self.worker = None

    def _on_sync_error(self, message: str) -> None:
        self.statusBar().showMessage(f"Sync failed: {message}", 4000)
        self.worker = None

    def _ai_parse_current(self) -> None:
        text = self.description_edit.toPlainText()
        dialog = AiParseDialog(self, initial_text=text)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.get_payload():
            payload = dialog.get_payload()
            if payload:
                self.title_edit.setText(payload["title"])
                self.description_edit.setPlainText(payload.get("description", ""))
                self.priority_combo.setCurrentText(payload.get("priority", "medium"))
                self.status_combo.setCurrentText(payload.get("status", "pending"))
                if payload.get("start_ts"):
                    start = datetime.fromisoformat(payload["start_ts"].replace("Z", "+00:00"))
                    self.start_edit.setDateTime(start.astimezone(self.config.timezone))
                if payload.get("due_ts"):
                    due = datetime.fromisoformat(payload["due_ts"].replace("Z", "+00:00"))
                    self.due_edit.setDateTime(due.astimezone(self.config.timezone))

    def _show_add_dialog(self) -> None:
        dialog = AiParseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            payload = dialog.get_payload()
            if not payload:
                QMessageBox.warning(self, "Add Task", "No parsed data available.")
                return
            start_ts = payload.get("start_ts")
            due_ts = payload.get("due_ts")
            start_dt = (
                datetime.fromisoformat(start_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
                if start_ts
                else None
            )
            due_dt = (
                datetime.fromisoformat(due_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
                if due_ts
                else None
            )
            with session_scope() as session:
                task = Task(
                    title=payload["title"],
                    description=payload.get("description", ""),
                    priority=payload.get("priority", "medium"),
                    status=payload.get("status", "pending"),
                    start_ts=start_dt,
                    due_ts=due_dt,
                    gcal_calendar_id=get_config().default_calendar_id,
                )
                session.add(task)
            self._load_tasks()
            self.statusBar().showMessage("Task added", 2000)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.scheduler.shutdown()
        super().closeEvent(event)


def launch_app() -> None:
    import sys

    app = QApplication(sys.argv)
    apply_dark_theme(app)
    scheduler = SchedulerManager()
    scheduler.start()
    window = MainWindow(scheduler)
    window.show()
    app.exec()
    scheduler.shutdown()

