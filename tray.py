"""
tray.py - system tray icon so the app keeps running (and reminding you)
in the background after you close the window.
"""

from config import APP_ID, APP_NAME

try:
    import pystray
    from assets import make_icon
    AVAILABLE = True
except Exception:
    AVAILABLE = False


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.running = False

    def start(self):
        if not AVAILABLE:
            return
        ui = self.app.call_in_ui
        menu = pystray.Menu(
            pystray.MenuItem("Open", lambda i, it: ui(self.app.show_window), default=True),
            pystray.MenuItem("New task", lambda i, it: ui(self.app.open_new_task_from_tray)),
            pystray.MenuItem("Quit", lambda i, it: ui(self.app.quit_app)),
        )
        try:
            self.icon = pystray.Icon(APP_ID, make_icon(64), APP_NAME, menu)
            self.icon.run_detached()
            self.running = True
        except Exception as e:
            print(f"[tray] could not start: {e}")
            self.running = False

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.running = False
