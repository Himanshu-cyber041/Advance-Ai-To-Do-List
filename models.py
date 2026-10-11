"""
models.py
---------
Task data structure shared by database, GUI, AI assistant and reminders.
"""

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

PRIORITIES = ["Low", "Medium", "High"]
CATEGORIES = ["General", "Work", "Personal", "Health", "Study"]
RECURRENCES = ["None", "Daily", "Weekdays", "Weekly", "Monthly"]
DATE_ONLY_REMINDER_HOUR = 9  # tasks with a date but no time remind at 09:00


@dataclass
class Task:
    title: str
    description: str = ""
    due_date: Optional[str] = None      # "YYYY-MM-DD"
    due_time: Optional[str] = None      # "HH:MM" (24-hour)
    priority: str = "Medium"            # Low | Medium | High
    category: str = "General"
    status: str = "Pending"             # Pending | Completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None
    # --- added in v2 ---
    recurrence: str = "None"            # None | Daily | Weekdays | Weekly | Monthly
    remind_before: int = 0              # minutes before due time
    notified: int = 0                   # 1 once the reminder has fired
    completed_at: Optional[str] = None
    snooze_until: Optional[str] = None  # "YYYY-MM-DDTHH:MM"

    # ------------------------------------------------------------------ #
    def due_datetime(self) -> Optional[datetime]:
        if not self.due_date:
            return None
        try:
            return datetime.strptime(f"{self.due_date} {self.due_time or '23:59'}", "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    def trigger_datetime(self) -> Optional[datetime]:
        """When the reminder should fire (None = never)."""
        if self.snooze_until:
            try:
                return datetime.fromisoformat(self.snooze_until)
            except ValueError:
                pass
        if not self.due_date:
            return None
        if not self.due_time:
            try:
                trig = datetime.strptime(
                    f"{self.due_date} {DATE_ONLY_REMINDER_HOUR:02d}:00", "%Y-%m-%d %H:%M")
                created = datetime.fromisoformat(self.created_at)
            except ValueError:
                return None
            # created later that same day -> user already knows, don't buzz instantly
            if created > trig:
                return None
            return trig
        due = self.due_datetime()
        return due - timedelta(minutes=max(0, self.remind_before)) if due else None

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        if self.status != "Pending":
            return False
        due = self.due_datetime()
        return bool(due and due < (now or datetime.now()))

    def next_due_date(self) -> Optional[str]:
        """Next occurrence for recurring tasks (always in the future)."""
        if not self.due_date or self.recurrence == "None":
            return None
        try:
            d = date.fromisoformat(self.due_date)
        except ValueError:
            return None
        today = date.today()

        def step(x: date) -> date:
            if self.recurrence == "Daily":
                return x + timedelta(days=1)
            if self.recurrence == "Weekly":
                return x + timedelta(days=7)
            if self.recurrence == "Weekdays":
                x += timedelta(days=1)
                while x.weekday() >= 5:
                    x += timedelta(days=1)
                return x
            if self.recurrence == "Monthly":
                month = x.month % 12 + 1
                year = x.year + (1 if x.month == 12 else 0)
                return x.replace(year=year, month=month,
                                 day=min(x.day, calendar.monthrange(year, month)[1]))
            return x + timedelta(days=1)

        nxt = step(d)
        while nxt <= today:
            nxt = step(nxt)
        return nxt.isoformat()

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "id", "title", "description", "due_date", "due_time", "priority",
            "category", "status", "created_at", "recurrence", "remind_before",
            "completed_at")}
