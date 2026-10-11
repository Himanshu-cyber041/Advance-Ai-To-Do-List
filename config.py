"""
config.py
---------
App-wide constants + user settings (saved in settings.json).

- Running from source  -> data lives next to the code.
- Running as .exe      -> data lives in %APPDATA%/AdvanceTodoAI so it
                          survives updates and works without admin rights.
The API key is entered in the Settings screen (no .env needed anymore,
but an old .env is still read as a fallback).
"""

import json
import os
import sys

APP_NAME = "Advance To-Do AI"
APP_ID = "AdvanceTodoAI"
FROZEN = getattr(sys, "frozen", False)


def _data_dir() -> str:
    if FROZEN:
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_ID)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(base, exist_ok=True)
    return base


DATA_DIR = _data_dir()
DB_PATH = os.path.join(DATA_DIR, "todo.db")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
LOG_PATH = os.path.join(DATA_DIR, "app.log")

try:  # optional legacy .env support
    from dotenv import load_dotenv
    load_dotenv(os.path.join(DATA_DIR, ".env"))
except Exception:
    pass

# --- GUI ---
WINDOW_SIZE = "1120x720"

# --- Reminders ---
REMINDER_CHECK_INTERVAL_SECONDS = 20

DEFAULT_SETTINGS = {
    "api_key": "",
    "model": "claude-sonnet-4-5",
    "voice_language": "en-IN",
    "tts_rate": 170,
    "mic_index": None,            # None = system default microphone
    "speak_reminders": True,
    "close_to_tray": True,
    "autostart": False,
    "default_remind_before": 10,  # minutes
}

_cache = None


def load_settings() -> dict:
    global _cache
    data = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    _cache = data
    return data


def get_setting(key: str):
    if _cache is None:
        load_settings()
    return _cache.get(key, DEFAULT_SETTINGS.get(key))


def save_settings(**changes) -> None:
    if _cache is None:
        load_settings()
    _cache.update(changes)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(_cache, f, indent=2)


def get_api_key() -> str:
    return (get_setting("api_key") or os.getenv("ANTHROPIC_API_KEY", "")).strip()
