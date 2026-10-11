"""
reminder.py
-----------
Background scheduler (APScheduler). Every few seconds it asks the database
which reminders are due, fires a desktop notification (plyer) and calls
on_reminder(task) so the GUI can show the popup (Done / Snooze).

"Already notified" is stored in the DATABASE, so restarting the app never
re-fires old reminders and snoozed tasks come back on time.
"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

import database
from config import APP_NAME, REMINDER_CHECK_INTERVAL_SECONDS

try:
    from plyer import notification
except Exception:  # plyer missing / unsupported platform
    notification = None


class ReminderService:
    def __init__(self, on_reminder=None):
        """on_reminder(task) runs on the scheduler thread - it must only hand
        data to the GUI thread (MainWindow.on_reminder_fired does that)."""
        self._scheduler = BackgroundScheduler()
        self.on_reminder = on_reminder

    def start(self):
        self._scheduler.add_job(
            self._check_due_tasks, "interval",
            seconds=REMINDER_CHECK_INTERVAL_SECONDS,
            id="due_task_check", replace_existing=True,
            next_run_time=datetime.now(),  # check immediately on start
        )
        self._scheduler.start()

    def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def _check_due_tasks(self):
        try:
            due = database.get_due_tasks(datetime.now())
        except Exception as e:
            print(f"[reminder] DB check failed: {e}")
            return
        for task in due:
            database.mark_notified(task.id)  # persist FIRST so it can never double-fire
            self._fire(task)

    def _fire(self, task):
        message = task.title
        if task.due_time:
            message += f"\nDue {task.due_time}"
        if task.description:
            message += f"\n{task.description}"
        if notification:
            try:
                notification.notify(title=f"{APP_NAME} - Reminder", message=message,
                                    app_name=APP_NAME, timeout=10)
            except Exception as e:
                print(f"[reminder] system notification failed: {e}")
        if self.on_reminder:
            try:
                self.on_reminder(task)
            except Exception as e:
                print(f"[reminder] on_reminder callback failed: {e}")
