"""Plague's Media Studio. Local, FFmpeg-based desktop media conversion."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PyQt6.QtCore import QSettings, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QScrollArea, QSplitter, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget, QLayout,
)

from theme import STYLE

APP = "Plague's Media Studio"
VERSION = "0.1.0"
FORMATS = (
    ("MP3", "mp3", "Audio"), ("WAV", "wav", "Audio"),
    ("FLAC", "flac", "Audio"), ("OGG", "ogg", "Audio"),
    ("M4A", "m4a", "Audio"), ("MP4", "mp4", "Video"),
    ("MKV", "mkv", "Video"), ("WebM", "webm", "Video"),
    ("AVI", "avi", "Video"), ("MOV", "mov", "Video"),
)
AUDIO = {fmt for _, fmt, kind in FORMATS if kind == "Audio"}


def asset(name: str) -> Path:
    """Find assets in source checkout or a PyInstaller one-folder installation."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "assets" / name


def app_icon() -> QIcon:
    path = asset("plagues-media-studio.png")
    return QIcon(str(path)) if path.is_file() else QIcon()


def human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return "?"


def output_path(source: str, folder: str, fmt: str, reserved: set[str]) -> Path:
    """Never overwrite existing media or collide with another queued output."""
    stem = Path(source).stem
    suffix = 1
    while True:
        label = stem if suffix == 1 else f"{stem} ({suffix})"
        candidate = Path(folder) / f"{label}.{fmt}"
        key = os.path.normcase(str(candidate.resolve()))
        if not candidate.exists() and key not in reserved:
            reserved.add(key)
            return candidate
        suffix += 1


class ConversionWorker(QThread):
    started_file = pyqtSignal(int, str)
    finished_file = pyqtSignal(int, str, str)
    progress = pyqtSignal(int, int)
    log_line = pyqtSignal(str)
    summary = pyqtSignal(int, int, bool)

    def __init__(self, paths: list[str], destination: str, fmt: str):
        super().__init__()
        self.paths, self.destination, self.fmt = paths, destination, fmt

    def run(self):
        success = failed = 0
        reserved: set[str] = set()
        cancelled = False
        total = len(self.paths)
        for index, source in enumerate(self.paths):
            if self.isInterruptionRequested():
                cancelled = True
                break
            target = output_path(source, self.destination, self.fmt, reserved)
            self.started_file.emit(index, Path(source).name)
            self.log_line.emit(f"Converting {source} → {target}")
            command = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
                       "-n", "-i", source]
            if self.fmt in AUDIO:
                command.append("-vn")
            command.append(str(target))
            try:
                # A temp file avoids blocking when FFmpeg emits many error messages.
                with tempfile.TemporaryFile(mode="w+t", encoding="utf-8", errors="replace") as err:
                    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=err)
                    while process.poll() is None:
                        if self.isInterruptionRequested():
                            cancelled = True
                            process.terminate()
                            try:
                                process.wait(timeout=3)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
                            break
                        time.sleep(0.15)
                    code = process.wait()
                    err.seek(0)
                    details = err.read()[-1800:].strip()
                if cancelled:
                    target.unlink(missing_ok=True)
                    self.finished_file.emit(index, "Cancelled", "Cancelled by user")
                    self.log_line.emit("Conversion cancelled.")
                    break
                if code == 0:
                    success += 1
                    self.finished_file.emit(index, "Complete", str(target))
                    self.log_line.emit(f"✓ Saved {target}")
                else:
                    failed += 1
                    target.unlink(missing_ok=True)
                    self.finished_file.emit(index, "Failed", details or "FFmpeg failed")
                    self.log_line.emit(f"✗ {Path(source).name}: {details or 'FFmpeg failed'}")
            except OSError as exc:
                failed += 1
                target.unlink(missing_ok=True)
                self.finished_file.emit(index, "Failed", str(exc))
                self.log_line.emit(f"✗ {exc}")
            self.progress.emit(index + 1, total)
        self.summary.emit(success, failed, cancelled)


class DropZone(QFrame):
    received = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setProperty("dragging", False)
        self.setAcceptDrops(True)
        area = QVBoxLayout(self)
        area.setContentsMargins(18, 18, 18, 17)
        area.setSpacing(5)
        title = QLabel("Drop audio or video files here")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #E8FAF7;")
        subtitle = QLabel("Or use Add files below. Files stay on your computer.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("HelpText")
        area.addWidget(title)
        area.addWidget(subtitle)

    def _highlight(self, enabled: bool):
        self.setProperty("dragging", enabled)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
            self._highlight(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._highlight(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._highlight(False)
        paths = [u.toLocalFile() for u in event.mimeData().urls()
                 if u.isLocalFile() and Path(u.toLocalFile()).is_file()]
        if paths:
            self.received.emit(paths)
            event.acceptProposedAction()


def line() -> QFrame:
    sep = QFrame()
    sep.setObjectName("HeaderLine")
    return sep


class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("PlaguedMods", "PlaguesMediaStudio")
        default_folder = Path.home() / "Videos"
        self.output = str(self.settings.value("destination", str(default_folder if default_folder.is_dir() else Path.home())))
        self.paths: list[str] = []
        self.worker: ConversionWorker | None = None
        self.running = False
        self.setWindowTitle(APP)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(900, 620)
        self.resize(1180, 750)
        self._build_menu()
        self._build_ui()
        self.setStyleSheet(STYLE)
        self._update_queue_count()
        self._update_ffmpeg()
        self._completion_note = ""
        saved_fmt = str(self.settings.value("format", "mp3"))
        index = self.format_combo.findData(saved_fmt)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)
        saved_geo = self.settings.value("geometry")
        if saved_geo:
            self.restoreGeometry(saved_geo)

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        add = QAction("Add media files…", self)
        add.setShortcut("Ctrl+O")
        add.triggered.connect(self.add_files)
        file_menu.addAction(add)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        help_menu = self.menuBar().addMenu("&Help")
        help_ffmpeg = QAction("FFmpeg requirements", self)
        help_ffmpeg.triggered.connect(self.ffmpeg_help)
        help_menu.addAction(help_ffmpeg)
        about = QAction("About Plague's Media Studio", self)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)

    def _build_ui(self):
        workspace = QWidget()
        workspace.setObjectName("Workspace")
        main = QVBoxLayout(workspace)
        main.setContentsMargins(24, 19, 24, 18)
        main.setSpacing(17)

        # Identity and working environment.
        header = QHBoxLayout()
        header.setSpacing(15)
        logo = QLabel()
        logo.setFixedSize(72, 72)
        pix = app_icon().pixmap(72, 72)
        logo.setPixmap(pix)
        header.addWidget(logo)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        eyebrow = QLabel("PLAGUED MODS  /  CREATIVE TOOLS")
        eyebrow.setObjectName("Eyebrow")
        name = QLabel(APP)
        name.setObjectName("BrandTitle")
        subtitle = QLabel("Audio & video conversion. Simple, local, and in your control.")
        subtitle.setObjectName("BrandSubtitle")
        brand.addWidget(eyebrow)
        brand.addWidget(name)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        badge_wrap = QVBoxLayout()
        badge_wrap.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.ffmpeg_badge = QFrame()
        badge_layout = QHBoxLayout(self.ffmpeg_badge)
        badge_layout.setContentsMargins(12, 7, 12, 7)
        self.ffmpeg_status = QLabel("Checking FFmpeg…")
        self.ffmpeg_status.setStyleSheet("font-size: 12px; font-weight: 700;")
        badge_layout.addWidget(self.ffmpeg_status)
        badge_wrap.addWidget(self.ffmpeg_badge)
        header.addLayout(badge_wrap)
        main.addLayout(header)
        main.addWidget(line())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(12)
        left = self._queue_panel()
        right = self._settings_panel()
        left.setMinimumWidth(500)
        right.setMinimumWidth(305)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([730, 395])
        main.addWidget(splitter, stretch=1)

        # Activity details remain optional, without hiding important status.
        activity_row = QHBoxLayout()
        self.activity_toggle = QPushButton("▸  Show activity log")
        self.activity_toggle.setObjectName("Quiet")
        self.activity_toggle.setCheckable(True)
        self.activity_toggle.toggled.connect(self._toggle_log)
        activity_row.addWidget(self.activity_toggle)
        activity_row.addStretch()
        self.summary_label = QLabel("Ready for new media")
        self.summary_label.setObjectName("StatusText")
        activity_row.addWidget(self.summary_label)
        main.addLayout(activity_row)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1500)
        self.log.setMinimumHeight(120)
        self.log.setMaximumHeight(170)
        self.log.hide()
        main.addWidget(self.log)
        self.setCentralWidget(workspace)
        self.statusBar().showMessage("Local processing · Your source files are never modified")

    def _queue_panel(self):
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(19, 19, 19, 19)
        layout.setSpacing(14)
        top = QHBoxLayout()
        heading = QLabel("Media queue")
        heading.setObjectName("SectionTitle")
        top.addWidget(heading)
        top.addStretch()
        self.queue_count = QLabel("0 files")
        self.queue_count.setObjectName("Muted")
        top.addWidget(self.queue_count)
        layout.addLayout(top)
        self.drop = DropZone()
        self.drop.received.connect(self.queue_files)
        layout.addWidget(self.drop)
        self.table = QTreeWidget()
        self.table.setColumnCount(4)
        self.table.setHeaderLabels(["MEDIA FILE", "TYPE", "SIZE", "STATUS"])
        self.table.setRootIsDecorated(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.table.setUniformRowHeights(True)
        self.table.setMinimumHeight(205)
        header = self.table.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setToolTip("Select one or more files and choose Remove selected")
        layout.addWidget(self.table, stretch=1)
        buttons = QHBoxLayout()
        self.add_btn = QPushButton("+  Add files")
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton("Remove selected")
        self.remove_btn.setObjectName("Quiet")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("Clear all")
        self.clear_btn.setObjectName("Quiet")
        self.clear_btn.clicked.connect(self.clear_queue)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.remove_btn)
        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        layout.addLayout(buttons)
        return panel

    def _settings_panel(self):
        panel = QFrame()
        panel.setObjectName("Panel")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(20, 17, 20, 17)
        outer.setSpacing(9)
        heading = QLabel("Conversion settings")
        heading.setObjectName("SectionTitle")
        outer.addWidget(heading)
        helper = QLabel("Choose the output format and where to save it.")
        helper.setObjectName("Muted")
        helper.setWordWrap(True)
        outer.addWidget(helper)

        # Keep input settings scrollable at compact window sizes; the important
        # progress and action controls remain visible at all times.
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { background: transparent; border: 0; }")
        settings_body = QWidget()
        settings_body.setObjectName("SettingsBody")
        layout = QVBoxLayout(settings_body)
        layout.setContentsMargins(1, 8, 5, 6)
        layout.setSpacing(9)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        format_label = QLabel("OUTPUT FORMAT")
        format_label.setObjectName("CardLabel")
        layout.addWidget(format_label)
        self.format_combo = QComboBox()
        for label, fmt, kind in FORMATS:
            self.format_combo.addItem(f"{label}   ·   {kind}", fmt)
        self.format_combo.currentIndexChanged.connect(self._update_format_hint)
        layout.addWidget(self.format_combo)
        self.format_hint = QLabel("Audio extraction supported")
        self.format_hint.setObjectName("FormatHint")
        self.format_hint.setWordWrap(True)
        layout.addWidget(self.format_hint)
        layout.addSpacing(9)
        destination_label = QLabel("SAVE CONVERTED FILES TO")
        destination_label.setObjectName("CardLabel")
        layout.addWidget(destination_label)
        self.folder_field = QLineEdit(self.output)
        self.folder_field.setReadOnly(True)
        self.folder_field.setToolTip(self.output)
        layout.addWidget(self.folder_field)
        browse_btn = QPushButton("Browse folders…")
        browse_btn.setObjectName("Quiet")
        browse_btn.clicked.connect(self.choose_folder)
        layout.addWidget(browse_btn)
        layout.addStretch(1)
        settings_scroll.setWidget(settings_body)
        outer.addWidget(settings_scroll, stretch=1)

        outer.addWidget(line())
        progress_title = QLabel("CONVERSION PROGRESS")
        progress_title.setObjectName("CardLabel")
        outer.addWidget(progress_title)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setFormat("0 / 0 processed")
        outer.addWidget(self.progress)
        self.current_file = QLabel("Nothing processing")
        self.current_file.setWordWrap(True)
        self.current_file.setObjectName("Muted")
        outer.addWidget(self.current_file)
        self.convert_btn = QPushButton("▶  Start conversion")
        self.convert_btn.setObjectName("Primary")
        self.convert_btn.clicked.connect(self.convert)
        outer.addWidget(self.convert_btn)
        self.cancel_btn = QPushButton("Cancel current job")
        self.cancel_btn.setObjectName("Danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        outer.addWidget(self.cancel_btn)
        notice = QLabel("Original files are kept. Existing outputs are never overwritten.")
        notice.setWordWrap(True)
        notice.setObjectName("HelpText")
        notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(notice)
        return panel

    def _update_format_hint(self, *_):
        fmt = self.format_combo.currentData()
        if fmt in AUDIO:
            self.format_hint.setText("Audio only · audio can be extracted from video")
        else:
            self.format_hint.setText("Video output · requires a compatible input stream")

    def _update_ffmpeg(self):
        good = shutil.which("ffmpeg") is not None
        self.ffmpeg_badge.setObjectName("StatusPill" if good else "MissingPill")
        self.ffmpeg_status.setText("●  FFmpeg ready" if good else "!  FFmpeg missing")
        self.ffmpeg_badge.style().unpolish(self.ffmpeg_badge)
        self.ffmpeg_badge.style().polish(self.ffmpeg_badge)
        self.convert_btn.setEnabled(good and bool(self.paths) and not self.running)
        self.ffmpeg_badge.setToolTip("FFmpeg command found in PATH" if good else "Install FFmpeg to enable conversion")

    def _toggle_log(self, visible: bool):
        self.log.setVisible(visible)
        self.activity_toggle.setText("▾  Hide activity log" if visible else "▸  Show activity log")

    def _update_queue_count(self):
        size = len(self.paths)
        self.queue_count.setText(f"{size} file{'s' if size != 1 else ''}")
        self.remove_btn.setEnabled(size > 0 and not self.running)
        self.clear_btn.setEnabled(size > 0 and not self.running)
        self.convert_btn.setEnabled(size > 0 and not self.running and bool(shutil.which("ffmpeg")))
        if not self.running:
            self.summary_label.setText("Ready for new media" if not size else f"{size} queued for conversion")

    def queue_files(self, incoming: list[str]):
        if self.running:
            return
        existing = {os.path.normcase(os.path.abspath(path)) for path in self.paths}
        for name in incoming:
            path = os.path.abspath(name)
            key = os.path.normcase(path)
            if key in existing or not os.path.isfile(path):
                continue
            existing.add(key)
            self.paths.append(path)
            file = Path(path)
            row = QTreeWidgetItem([file.name, file.suffix[1:].upper() or "MEDIA",
                                   human_size(file.stat().st_size), "Queued"])
            row.setToolTip(0, path)
            self.table.addTopLevelItem(row)
        self._update_queue_count()

    def add_files(self):
        if self.running:
            return
        dialog = QFileDialog(self, "Add media files")
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("Media files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.opus *.mp4 *.mkv *.webm *.avi *.mov *.wmv *.m4v);;All files (*)")
        dialog.setWindowIcon(app_icon())
        if dialog.exec():
            self.queue_files(dialog.selectedFiles())

    def remove_selected(self):
        if self.running:
            return
        indexes = sorted({self.table.indexOfTopLevelItem(item) for item in self.table.selectedItems()}, reverse=True)
        for index in indexes:
            if index >= 0:
                self.table.takeTopLevelItem(index)
                self.paths.pop(index)
        self._update_queue_count()

    def clear_queue(self):
        if self.running:
            return
        self.paths.clear()
        self.table.clear()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setFormat("0 / 0 processed")
        self.current_file.setText("Nothing processing")
        self._update_queue_count()

    def choose_folder(self):
        if self.running:
            return
        dialog = QFileDialog(self, "Select output folder", self.output)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setWindowIcon(app_icon())
        if dialog.exec() and dialog.selectedFiles():
            self.output = dialog.selectedFiles()[0]
            self.folder_field.setText(self.output)
            self.folder_field.setToolTip(self.output)

    def _message(self, title: str, message: str, kind: QMessageBox.Icon):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setWindowIcon(app_icon())
        dialog.setText(message)
        pix = app_icon().pixmap(64, 64)
        if not pix.isNull():
            dialog.setIconPixmap(pix)
        else:
            dialog.setIcon(kind)
        dialog.exec()

    def ffmpeg_help(self):
        self._message("FFmpeg requirements",
            "FFmpeg must be installed and available on PATH.\n\n"
            "Debian/Ubuntu: sudo apt install ffmpeg\n"
            "Fedora: install the ffmpeg package from an enabled repository\n"
            "Windows: install FFmpeg and add its bin folder to PATH.\n\n"
            "Restart the application after installing FFmpeg.", QMessageBox.Icon.Information)

    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"About {APP}")
        dialog.setWindowIcon(app_icon())
        dialog.setMinimumWidth(445)
        box = QVBoxLayout(dialog)
        box.setContentsMargins(32, 30, 32, 28)
        box.setSpacing(12)
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(app_icon().pixmap(110, 110))
        box.addWidget(logo)
        title = QLabel(APP)
        title.setObjectName("BrandTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(title)
        version = QLabel(f"Version {VERSION}  ·  Audio & Video Tools")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setObjectName("Muted")
        box.addWidget(version)
        box.addWidget(line())
        body = QLabel("A local-first media conversion tool powered by FFmpeg.\n"
                      "Convert audio and video without uploading your files.")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        box.addWidget(body)
        credit = QLabel("Created by Kaotick Jay  ·  Plagued Mods")
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit.setObjectName("Eyebrow")
        box.addWidget(credit)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        box.addWidget(close)
        dialog.setStyleSheet(STYLE)
        dialog.exec()

    def _set_running(self, running: bool):
        self.running = running
        for widget in (self.add_btn, self.remove_btn, self.clear_btn, self.format_combo):
            widget.setEnabled(not running)
        self.drop.setAcceptDrops(not running)
        self.cancel_btn.setEnabled(running)
        self.cancel_btn.setVisible(running)
        self._update_queue_count()

    def convert(self):
        if self.running:
            return
        if not self.paths:
            self._message(APP, "Add one or more media files first.", QMessageBox.Icon.Information)
            return
        if not shutil.which("ffmpeg"):
            self.ffmpeg_help()
            return
        try:
            os.makedirs(self.output, exist_ok=True)
            if not os.path.isdir(self.output) or not os.access(self.output, os.W_OK):
                raise OSError("Output folder is not writable")
        except OSError as exc:
            self._message("Cannot use output folder", str(exc), QMessageBox.Icon.Critical)
            return
        self._completion_note = ""
        self.table.clearSelection()
        for i in range(self.table.topLevelItemCount()):
            self.table.topLevelItem(i).setText(3, "Queued")
            self.table.topLevelItem(i).setToolTip(3, "")
        fmt = str(self.format_combo.currentData())
        self.settings.setValue("format", fmt)
        self.settings.setValue("destination", self.output)
        self.progress.setRange(0, len(self.paths))
        self.progress.setValue(0)
        self.progress.setFormat(f"0 / {len(self.paths)} processed")
        self.summary_label.setText("Processing media…")
        self._set_running(True)
        self.worker = ConversionWorker(self.paths[:], self.output, fmt)
        self.worker.started_file.connect(self._on_start)
        self.worker.finished_file.connect(self._on_item_done)
        self.worker.progress.connect(self._on_progress)
        self.worker.log_line.connect(self.log.appendPlainText)
        self.worker.summary.connect(self._on_summary)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _on_start(self, index: int, name: str):
        self.table.topLevelItem(index).setText(3, "Converting…")
        self.current_file.setText(name)

    def _on_item_done(self, index: int, state: str, details: str):
        self.table.topLevelItem(index).setText(3, state)
        self.table.topLevelItem(index).setToolTip(3, details)

    def _on_progress(self, completed: int, total: int):
        self.progress.setValue(completed)
        self.progress.setFormat(f"{completed} / {total} processed")

    def cancel_conversion(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.cancel_btn.setEnabled(False)
            self.summary_label.setText("Cancelling…")

    def _on_summary(self, success: int, failed: int, cancelled: bool):
        note = "Cancelled" if cancelled else "Finished"
        self.summary_label.setText(f"{note} · {success} successful · {failed} failed")
        self.current_file.setText("Conversion cancelled" if cancelled else "Conversion complete")
        self.log.appendPlainText(f"{note}: {success} completed, {failed} failed")
        self._completion_note = f"{note} · {success} successful · {failed} failed"

    def _worker_finished(self):
        self._set_running(False)
        if self._completion_note:
            self.summary_label.setText(self._completion_note)
        self.worker = None
        self._update_ffmpeg()

    def closeEvent(self, event: QCloseEvent):
        if self.worker and self.worker.isRunning():
            result = QMessageBox.question(
                self, "Conversion still running", "Cancel the conversion and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if result != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.worker.requestInterruption()
            self.worker.wait()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("destination", self.output)
        self.settings.setValue("format", self.format_combo.currentData())
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setOrganizationName("Plagued Mods")
    app.setWindowIcon(app_icon())
    window = Studio()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())