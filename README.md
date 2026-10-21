# Plague's Media Studio

Cross-platform media conversion studio by **Kaotick Jay / Plagued Mods**.

This is a **new source reconstruction**, not a byte-for-byte restoration of the October 2026 Media Conversion Suite APK. That archived source was not available during this import.

## Features
- Windows and Linux: PyQt6 GUI; FFmpeg/FFprobe-backed conversion; queue, format presets, progress and logs.
- Android: Native Java picker and on-device FFmpeg conversion; output placed in the user's selected destination.
- Nine target containers/formats: mp3, wav, flac, ogg, m4a, mp4, mkv, webm, avi, mov.
- No XWM on Android. Downloading support from the original app is **not yet ported**.

## Desktop
Install Python 3.11+, FFmpeg and FFprobe in PATH. Run:
```sh
python -m pip install -r requirements.txt
python desktop/main.py
```
### CI downloads
[Actions](../../actions) produces a Windows setup EXE, a Linux .deb and AppImage-style portable directory archive, and an Android development APK (if all dependencies resolve). Artifacts are uploaded by each workflow.

## Android
Requires Android SDK 35, Java 17 and Gradle 8.10.2. Uses maintained FFmpegKit 8.1.9. The download from Actions is debug-signed and **not** a production signing identity.

## Provenance
The legacy desktop application was Media Conversion Suite v1.7.1. This repository establishes the renamed project; old implementation-specific features must be audited before claiming feature parity.

## Third-party notice
FFmpeg and its codec dependencies have their own licenses. Review codec and redistribution obligations before shipping an installer commercially.

## Desktop GUI (studio workspace)
The desktop GUI now includes a high-contrast, two-panel layout with the custom Plague's Media Studio icon in the header, About dialog, application window and confirmation dialogs. Drag-and-drop import, a readable conversion queue, separate output controls, optional activity log, progress status, cancellation, remembered settings and collision-safe output filenames are included. FFmpeg must be installed and on PATH; converted output is never allowed to overwrite an existing file. The embedded icon is also supplied to the Windows PyInstaller executable, Windows installer and Linux desktop launcher.
