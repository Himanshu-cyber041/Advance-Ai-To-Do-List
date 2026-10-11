"""
main.py - entry point.
    python main.py              normal start
    python main.py --minimized  start hidden in the system tray (used by autostart)
"""

import socket
import sys

import config

if sys.stdout is None or sys.stderr is None:  # windowed .exe has no console
    _log = open(config.LOG_PATH, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log


def _single_instance():
    """Only one copy may run (two copies = double reminders)."""
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 47653))
        s.listen(1)
        return s
    except OSError:
        return None


def main():
    lock = _single_instance()
    if lock is None:
        print("Already running - check the system tray.")
        return

    from database import init_db
    from gui.main_window import MainWindow
    from reminder import ReminderService
    from tray import TrayIcon

    init_db()  # creates / migrates todo.db
    app = MainWindow()
    app.report_callback_exception = lambda *a: print("[tk error]", *a)

    service = ReminderService(on_reminder=app.on_reminder_fired)
    service.start()
    app.reminder_service = service

    tray = TrayIcon(app)
    tray.start()
    app.tray = tray

    if "--minimized" in sys.argv and tray.running:
        app.after(700, app.withdraw)

    try:
        app.mainloop()
    finally:
        service.stop()
        tray.stop()


if __name__ == "__main__":
    main()
