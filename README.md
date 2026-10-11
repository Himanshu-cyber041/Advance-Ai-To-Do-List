# ✦ Advance To-Do AI

A desktop to-do manager built for daily use: type or speak tasks in English or Hinglish, get reminders that actually reach you, and track your habits, all in a dark-luxury interface with smooth animations.

Built with **Python**, **CustomTkinter** and the **Anthropic API**. Ships as a single Windows `.exe`.

---

## Features

### Task management
- Create, edit, complete, delete tasks with **undo** after delete
- Views: **Today**, **Upcoming**, **All tasks**, **Completed**, **Insights**
- Priority (Low / Medium / High), categories, notes, due date and time
- **Recurring tasks**: Daily, Weekdays, Weekly, Monthly. The next occurrence is created automatically on completion
- Live **search** and **category filter**

### AI and voice
- **Natural-language quick add**: `kal shaam 6 baje mummy ko call, high priority`
- Understands English, Hindi and Hinglish; resolves relative dates ("tomorrow", "kal", "next Monday")
- **Offline fallback parser**: works without an API key or internet connection
- **Voice input** (Google speech recognition, language selectable) with a confirmation dialog before saving
- **Smart suggestions**: Claude analyses your history and proposes tasks you usually repeat
- **Daily briefing** spoken aloud

### Reliable reminders
- Background scheduler with desktop notifications and an in-app popup
- **Done / Snooze 10 min / Snooze 1 hour** directly from the reminder
- Configurable lead time ("10 minutes before")
- "Already notified" state is stored in the database, so restarting the app never re-fires old reminders
- Runs in the **system tray**, with optional **start with Windows**
- Single-instance lock prevents duplicate reminders

### Interface
- Dark-luxury theme (black and gold), rounded cards, priority colour strips
- Animations: window fade-in, staggered card fade-in, hover glow, completion collapse, animated progress ring, sliding toasts, pulsing microphone, growing charts
- **Insights**: day streak, weekly completion chart, category breakdown

---

## Tech stack

| Area | Library |
|---|---|
| GUI | `customtkinter`, `tkinter` |
| AI | `anthropic` |
| Storage | `sqlite3` (standard library) |
| Scheduling | `apscheduler` |
| Notifications / tray | `plyer`, `pystray`, `pillow` |
| Voice | `speechrecognition`, `pyaudio`, `pyttsx3` |
| Packaging | `pyinstaller` |

---

## Project structure

```
todo_ai/
├── main.py                 # entry point (single instance, tray, scheduler)
├── config.py               # paths + persistent settings (settings.json)
├── models.py               # Task dataclass, recurrence and reminder logic
├── database.py             # all SQLite access + migration from v1 databases
├── ai_assistant.py         # parsing (AI + offline), suggestions, briefing
├── reminder.py             # background reminder service
├── voice_handler.py        # speech-to-text and text-to-speech
├── tray.py                 # system tray icon
├── system_integration.py   # Windows autostart
├── assets.py               # app icon generated in code
├── test_mic.py             # microphone diagnostic tool
├── build.py / build.bat    # build the .exe
├── installer.iss           # optional Inno Setup installer script
├── requirements.txt
└── gui/
    ├── main_window.py      # main window, views, quick add, insights
    ├── widgets.py          # TaskCard, ProgressRing, Toast
    ├── task_dialog.py      # create / edit dialog
    ├── dialogs.py          # reminder popup, settings dialog
    └── theme.py            # palette + animation engine
```

---

## Getting started

### Requirements
- Python 3.10 or newer (tested with 3.12; 3.13 works if `pyaudio` installs)
- Windows 10/11 recommended (tray, autostart, notifications and voice are built for Windows)
- Optional: an [Anthropic API key](https://console.anthropic.com/) for AI parsing and suggestions

### Run from source

```bash
git clone <your-repo-url>
cd todo_ai

python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

python main.py
```

Use `python main.py --minimized` to start hidden in the tray.

### First-time setup
1. Open **Settings** (sidebar).
2. Paste your **Anthropic API key** and press **Test connection**.
3. Choose your **microphone** and speech language.
4. Choose whether to keep running in the tray and start with Windows.

The app works without a key; quick add then uses the offline parser and AI suggestions are unavailable.

---

## Build a Windows executable

```bash
build.bat
```

or manually:

```bash
pip install -r requirements.txt
python build.py
```

Output: `dist/AdvanceTodoAI.exe`, which needs no Python installed. For a proper installer with Start-menu and desktop shortcuts, compile `installer.iss` with [Inno Setup](https://jrsoftware.org/isinfo.php).

---

## Usage

### Quick add examples
| You type or say | Result |
|---|---|
| `kal shaam 6 baje mummy ko call, high priority` | Tomorrow 18:00, High, Personal |
| `remind me to take medicine every day at 8am` | Daily 08:00, Health |
| `submit report on friday at 5pm urgent` | Friday 17:00, High, Work |
| `buy milk` | Undated task in Today under "Anytime" |

### Keyboard shortcuts
| Shortcut | Action |
|---|---|
| `Ctrl + N` | New task |
| `Ctrl + F` | Focus search |
| `Enter` | Submit quick add / save dialog |
| `Esc` | Close dialog |

### Reminder behaviour
- Tasks with a time remind at *due time minus lead time*.
- Tasks with a date but no time remind at 09:00 on that day (unless created later the same day).
- Snoozed tasks return at the snooze time. Overdue reminders fire once.

---

## Data and privacy

| Item | Location |
|---|---|
| From source | next to the code (`todo.db`, `settings.json`) |
| As `.exe` | `%APPDATA%\AdvanceTodoAI\` |
| Logs | `app.log` in the data folder |

- Tasks are stored locally in SQLite.
- Task text is sent to the Anthropic API **only** when you add a task by quick add or voice with an API key set, or request suggestions. Voice audio is sent to Google's speech service for recognition.
- The API key is stored in `settings.json` on your machine. Never commit it; the included `.gitignore` already excludes it.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `pyaudio` fails to install | Use Python 3.12, or `pip install pipwin` then `pipwin install pyaudio` |
| Mic not detected | Run `python test_mic.py`, then choose the device in Settings. Check Windows Settings > Privacy > Microphone |
| No desktop notifications | The in-app popup still appears. Check Windows notification and focus-assist settings |
| `.exe` voice or notifications missing | Rebuild with `build.py` (hidden imports are included) and check `app.log` |
| "Already running" | The app is in the system tray; use the tray icon to open or quit |
| AI parsing falls back to offline | Check the API key and internet in Settings > Test connection |

---

## Roadmap
- Subtasks and checklists
- Calendar (ICS / Google) sync
- Light theme and custom accent colours
- Data export / import

---

## License

Add your preferred license here (for example MIT) before publishing.
