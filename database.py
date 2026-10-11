"""
database.py
-----------
All SQLite operations. Other modules never touch SQL directly.
init_db() also migrates an old v1 database (adds the new columns safely).
"""

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import List, Optional

from config import DB_PATH
from models import Task


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


_NEW_COLUMNS = {
    "recurrence": "TEXT DEFAULT 'None'",
    "remind_before": "INTEGER DEFAULT 0",
    "notified": "INTEGER DEFAULT 0",
    "completed_at": "TEXT",
    "snooze_until": "TEXT",
}


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                due_time TEXT,
                priority TEXT DEFAULT 'Medium',
                category TEXT DEFAULT 'General',
                status TEXT DEFAULT 'Pending',
                created_at TEXT,
                recurrence TEXT DEFAULT 'None',
                remind_before INTEGER DEFAULT 0,
                notified INTEGER DEFAULT 0,
                completed_at TEXT,
                snooze_until TEXT
            )
        """)
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(tasks)")}
        today = date.today().isoformat()
        for col, ddl in _NEW_COLUMNS.items():
            if col in existing:
                continue
            conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {ddl}")
            if col == "notified":  # don't spam alerts for old overdue tasks
                conn.execute("UPDATE tasks SET notified=1 WHERE due_date IS NOT NULL AND due_date < ?", (today,))
                conn.execute("UPDATE tasks SET notified=1 WHERE status='Completed'")
            if col == "completed_at":
                conn.execute("UPDATE tasks SET completed_at=created_at WHERE status='Completed'")


# ---------------------------------------------------------------------- #
# CRUD
# ---------------------------------------------------------------------- #
def add_task(task: Task) -> int:
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO tasks (title, description, due_date, due_time, priority, category,
                               status, created_at, recurrence, remind_before, notified,
                               completed_at, snooze_until)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (task.title, task.description, task.due_date, task.due_time, task.priority,
              task.category, task.status, task.created_at, task.recurrence,
              task.remind_before, task.notified, task.completed_at, task.snooze_until))
        return cur.lastrowid


def get_all_tasks(status: Optional[str] = None) -> List[Task]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status=? ORDER BY due_date, due_time", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks ORDER BY due_date, due_time").fetchall()
        return [_row_to_task(r) for r in rows]


def get_task_by_id(task_id: int) -> Optional[Task]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None


def update_task(task: Task):
    """Re-arms the reminder automatically if the schedule changed."""
    if task.id is None:
        raise ValueError("Cannot update a task without an id")
    old = get_task_by_id(task.id)
    rearm = old is None or (old.due_date, old.due_time, old.remind_before) != \
        (task.due_date, task.due_time, task.remind_before)
    with get_connection() as conn:
        conn.execute("""
            UPDATE tasks SET title=?, description=?, due_date=?, due_time=?, priority=?,
                             category=?, status=?, recurrence=?, remind_before=?
            WHERE id=?
        """, (task.title, task.description, task.due_date, task.due_time, task.priority,
              task.category, task.status, task.recurrence, task.remind_before, task.id))
        if rearm:
            conn.execute("UPDATE tasks SET notified=0, snooze_until=NULL WHERE id=?", (task.id,))


def delete_task(task_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))


def mark_completed(task_id: int) -> Optional[Task]:
    """Completes a task. If it repeats, creates the next one and returns it."""
    task = get_task_by_id(task_id)
    if not task or task.status == "Completed":
        return None
    with get_connection() as conn:
        conn.execute("UPDATE tasks SET status='Completed', completed_at=?, notified=1 WHERE id=?",
                     (datetime.now().isoformat(timespec="seconds"), task_id))
    nxt = task.next_due_date()
    if not nxt:
        return None
    new = Task(title=task.title, description=task.description, due_date=nxt,
               due_time=task.due_time, priority=task.priority, category=task.category,
               recurrence=task.recurrence, remind_before=task.remind_before)
    new.id = add_task(new)
    return new


def reopen_task(task_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE tasks SET status='Pending', completed_at=NULL, notified=1 WHERE id=?", (task_id,))


# ---------------------------------------------------------------------- #
# Reminders
# ---------------------------------------------------------------------- #
def get_due_tasks(now=None) -> List[Task]:
    """Pending, not-yet-notified tasks whose reminder time has arrived."""
    if isinstance(now, str):
        now = datetime.strptime(now, "%Y-%m-%d %H:%M")
    now = now or datetime.now()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tasks WHERE status='Pending' AND notified=0
            AND (due_date IS NOT NULL OR snooze_until IS NOT NULL)
        """).fetchall()
    due = []
    for r in rows:
        t = _row_to_task(r)
        trig = t.trigger_datetime()
        if trig and trig <= now:
            due.append(t)
    return due


def mark_notified(task_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE tasks SET notified=1, snooze_until=NULL WHERE id=?", (task_id,))


def snooze_task(task_id: int, minutes: int):
    until = (datetime.now() + timedelta(minutes=minutes)).isoformat(timespec="minutes")
    with get_connection() as conn:
        conn.execute("UPDATE tasks SET snooze_until=?, notified=0 WHERE id=?", (until, task_id))


# ---------------------------------------------------------------------- #
# AI + stats
# ---------------------------------------------------------------------- #
def get_task_history_for_ai(limit: int = 100) -> List[Task]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [_row_to_task(r) for r in rows]


def get_stats() -> dict:
    today = date.today()
    t = today.isoformat()
    with get_connection() as conn:
        def one(sql, args=()):
            return conn.execute(sql, args).fetchone()[0]

        total_today = one("SELECT COUNT(*) FROM tasks WHERE due_date=?", (t,))
        done_today = one("SELECT COUNT(*) FROM tasks WHERE due_date=? AND status='Completed'", (t,))
        overdue = one("SELECT COUNT(*) FROM tasks WHERE status='Pending' AND due_date IS NOT NULL AND due_date<?", (t,))
        pending = one("SELECT COUNT(*) FROM tasks WHERE status='Pending'")
        completed_total = one("SELECT COUNT(*) FROM tasks WHERE status='Completed'")
        rows = conn.execute("""
            SELECT substr(completed_at,1,10) AS d, COUNT(*) AS c FROM tasks
            WHERE status='Completed' AND completed_at IS NOT NULL GROUP BY d
        """).fetchall()
        cats = conn.execute("""
            SELECT category, COUNT(*) AS c FROM tasks WHERE status='Completed'
            GROUP BY category ORDER BY c DESC
        """).fetchall()

    per_day = {r["d"]: r["c"] for r in rows}
    week = [((today - timedelta(days=i)).isoformat(), per_day.get((today - timedelta(days=i)).isoformat(), 0))
            for i in range(6, -1, -1)]
    streak, d = 0, today
    if not per_day.get(d.isoformat()):
        d -= timedelta(days=1)
    while per_day.get(d.isoformat()):
        streak += 1
        d -= timedelta(days=1)

    return {
        "total_today": total_today, "done_today": done_today, "overdue": overdue,
        "pending": pending, "completed_total": completed_total, "streak": streak,
        "week": week, "week_total": sum(c for _, c in week),
        "categories": [(r["category"] or "General", r["c"]) for r in cats],
    }


def _row_to_task(row: sqlite3.Row) -> Task:
    keys = row.keys()

    def g(name, default=None):
        return row[name] if name in keys and row[name] is not None else default

    return Task(
        id=row["id"], title=row["title"], description=g("description", ""),
        due_date=g("due_date"), due_time=g("due_time"),
        priority=g("priority", "Medium"), category=g("category", "General"),
        status=g("status", "Pending"), created_at=g("created_at", datetime.now().isoformat()),
        recurrence=g("recurrence", "None"), remind_before=g("remind_before", 0),
        notified=g("notified", 0), completed_at=g("completed_at"),
        snooze_until=g("snooze_until"),
    )
