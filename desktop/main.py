"""Plague's Media Studio - desktop media converter."""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QComboBox, QVBoxLayout, QWidget, QListWidget)

APP = "Plague's Media Studio"
FORMATS = ("mp3", "wav", "flac", "ogg", "m4a", "mp4", "mkv", "webm", "avi", "mov")
AUDIO = {"mp3", "wav", "flac", "ogg", "m4a"}

class Worker(QThread):
    status = pyqtSignal(str)
    done = pyqtSignal(int, int)
    def __init__(self, sources: list[str], dest: str, fmt: str):
        super().__init__()
        self.sources, self.dest, self.fmt = sources, dest, fmt
    def run(self):
        success = 0
        for i, source in enumerate(self.sources):
            target = Path(self.dest) / (Path(source).stem + "." + self.fmt)
            if target.exists():
                self.status.emit(f"Skipped (exists): {target}")
                continue
            cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", source]
            if self.fmt in AUDIO:
                cmd += ["-vn"]
            cmd += ["-y", str(target)]
            self.status.emit(f"Converting {Path(source).name} -> {target.name}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    success += 1
                    self.status.emit(f"Saved: {target}")
                else:
                    target.unlink(missing_ok=True)
                    self.status.emit(f"ERROR: {result.stderr[-2000:]}")
            except OSError as error:
                self.status.emit(f"ERROR: {error}")
            self.done.emit(i + 1, success)

class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP)
        self.resize(850, 590)
        self.files: list[str] = []
        self.output = str(Path.home() / "Videos")
        center = QWidget()
        layout = QVBoxLayout(center)
        heading = QLabel(APP)
        heading.setStyleSheet("font-size: 23px; font-weight: bold; padding: 9px;")
        layout.addWidget(heading)
        self.listing = QListWidget()
        layout.addWidget(self.listing)
        row = QHBoxLayout()
        add = QPushButton("Add files")
        add.clicked.connect(self.add_files)
        clear = QPushButton("Clear queue")
        clear.clicked.connect(self.clear_files)
        row.addWidget(add)
        row.addWidget(clear)
        layout.addLayout(row)
        row2 = QHBoxLayout()
        self.folder = QLabel(self.output)
        choose = QPushButton("Destination…")
        choose.clicked.connect(self.choose_folder)
        row2.addWidget(self.folder, 1)
        row2.addWidget(choose)
        layout.addLayout(row2)
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Output format"))
        self.format = QComboBox()
        self.format.addItems(FORMATS)
        row3.addWidget(self.format)
        self.go = QPushButton("Convert queue")
        self.go.clicked.connect(self.convert)
        row3.addWidget(self.go)
        layout.addLayout(row3)
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        self.setCentralWidget(center)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #121a25; color: #e6edf4; }
            QPushButton, QComboBox { background: #20364a; border: 1px solid #436b7e; padding: 8px; }
            QListWidget, QPlainTextEdit { background: #0d1520; border: 1px solid #365064; }
            QProgressBar { border: 1px solid #436b7e; text-align: center; }
            QProgressBar::chunk { background: #238c9c; }
        """)
    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add media")
        for path in paths:
            if path not in self.files:
                self.files.append(path)
                self.listing.addItem(path)
    def clear_files(self):
        self.files.clear()
        self.listing.clear()
    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Output folder", self.output)
        if path:
            self.output = path
            self.folder.setText(path)
    def convert(self):
        if not self.files:
            QMessageBox.information(self, APP, "Add media files first.")
            return
        if shutil.which("ffmpeg") is None:
            QMessageBox.critical(self, APP, "FFmpeg is missing from PATH.")
            return
        os.makedirs(self.output, exist_ok=True)
        self.go.setEnabled(False)
        self.progress.setMaximum(len(self.files))
        self.progress.setValue(0)
        self.worker = Worker(self.files[:], self.output, self.format.currentText())
        self.worker.status.connect(self.log.appendPlainText)
        self.worker.done.connect(self.on_progress)
        self.worker.finished.connect(lambda: self.go.setEnabled(True))
        self.worker.start()
    def on_progress(self, count, successful):
        self.progress.setValue(count)
        if count == len(self.files):
            self.log.appendPlainText(f"Finished: {successful}/{count} converted.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Studio()
    window.show()
    sys.exit(app.exec())
