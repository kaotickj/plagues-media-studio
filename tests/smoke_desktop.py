"""Headless Qt smoke test plus visual snapshot for GitHub Actions."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktop"))

from PyQt6.QtWidgets import QApplication  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402
from main import ConversionWorker, Studio, output_path  # noqa: E402


def main():
    app = QApplication([])
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        source = folder / "example.wav"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
             "sine=frequency=440:duration=0.25", "-y", str(source)],
            check=True,
        )

        reserved: set[str] = set()
        target = output_path(str(source), temp, "mp3", reserved)
        assert target.name == "example.mp3"
        second = output_path(str(source), temp, "mp3", reserved)
        assert second.name == "example (2).mp3"

        # Exercise the actual converter without risking a user's media.
        worker = ConversionWorker([str(source)], temp, "mp3")
        worker.run()
        assert target.is_file() and target.stat().st_size > 100

        studio = Studio()
        studio.queue_files([str(source)])
        assert studio.table.topLevelItemCount() == 1
        studio.resize(1180, 750)
        studio.show()
        app.processEvents()
        screenshot = ROOT / "dist" / "studio-preview.png"
        screenshot.parent.mkdir(exist_ok=True)
        assert studio.grab().save(str(screenshot), "PNG")
        assert screenshot.stat().st_size > 10_000
        another = folder / "another.wav"
        another.write_bytes(source.read_bytes())
        studio.queue_files([str(another)])
        studio.table.sortItems(0, Qt.SortOrder.DescendingOrder)
        selected = studio.table.topLevelItem(0)
        selected_path = selected.data(0, Qt.ItemDataRole.UserRole)
        selected.setSelected(True)
        studio.remove_selected()
        assert selected_path not in studio.paths
        assert studio.table.topLevelItemCount() == 1
        studio.clear_queue()
        assert studio.table.topLevelItemCount() == 0
        studio.close()
    print("GUI initialization, media queue, FFmpeg conversion and screenshot: PASS")


if __name__ == "__main__":
    main()