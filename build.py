"""
build.py - makes a single-file Windows program:   python build.py
Result: dist/AdvanceTodoAI.exe  (double-click, no Python needed)
"""

import subprocess
import sys

import assets

assets.save_ico("icon.ico")

cmd = [
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
    "--onefile", "--windowed",
    "--name", "AdvanceTodoAI",
    "--icon", "icon.ico",
    "--collect-all", "customtkinter",
    "--collect-all", "speech_recognition",   # ships the flac converter Google STT needs
    "--collect-submodules", "anthropic",
    "--collect-submodules", "apscheduler",
    "--hidden-import", "plyer.platforms.win.notification",
    "--hidden-import", "pystray._win32",
    "--hidden-import", "pyttsx3.drivers",
    "--hidden-import", "pyttsx3.drivers.sapi5",
    "main.py",
]
print(" ".join(cmd))
sys.exit(subprocess.call(cmd))
