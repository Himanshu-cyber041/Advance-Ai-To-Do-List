"""system_integration.py - Windows autostart (HKCU Run key, no admin needed)."""

import os
import sys

from config import APP_ID, FROZEN

try:
    import winreg
except ImportError:  # not Windows
    winreg = None

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def supported() -> bool:
    return winreg is not None


def _command() -> str:
    if FROZEN:
        return f'"{sys.executable}" --minimized'
    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    main = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{pyw}" "{main}" --minimized'


def is_autostart() -> bool:
    if not winreg:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_ID)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> bool:
    if not winreg:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, APP_ID, 0, winreg.REG_SZ, _command())
            else:
                try:
                    winreg.DeleteValue(k, APP_ID)
                except FileNotFoundError:
                    pass
        return True
    except OSError as e:
        print(f"[autostart] failed: {e}")
        return False
