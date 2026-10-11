"""
ai_assistant.py
----------------
  1. parse_task()  - natural sentence (English / Hinglish) -> Task.
                     Uses Claude if an API key is set, otherwise (or if the
                     network/API fails) a built-in offline parser, so adding
                     tasks NEVER breaks.
  2. suggest_tasks_from_history() - habit-based suggestions (needs API key).
  3. build_briefing() - local "what's on today" summary (no API needed).
"""

import json
import re
from datetime import date, datetime, timedelta
from typing import Optional

import config
from models import Task, PRIORITIES, CATEGORIES, RECURRENCES


class AIAssistantError(Exception):
    pass


_client = None
_client_key = None


def _get_client():
    global _client, _client_key
    key = config.get_api_key()
    if not key:
        raise AIAssistantError("API key not set. Open Settings and paste your Anthropic API key.")
    if _client is None or key != _client_key:
        from anthropic import Anthropic  # lazy import: offline mode works without it
        _client = Anthropic(api_key=key)
        _client_key = key
    return _client


def _extract_json(raw: str):
    raw = raw.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    starts = [i for i in (raw.find("{"), raw.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON found")
    start = min(starts)
    end = max(raw.rfind("}"), raw.rfind("]"))
    return json.loads(raw[start:end + 1])


# ---------------------------------------------------------------------- #
# 1. Natural language -> Task
# ---------------------------------------------------------------------- #
def _roll_forward(task: Task) -> Task:
    """A repeating task whose first time already passed starts at its next occurrence."""
    if task.recurrence != "None" and task.is_overdue():
        task.due_date = task.next_due_date() or task.due_date
    return task


def parse_task(text: str):
    """Returns (Task, source) where source is 'ai' or 'offline'."""
    if config.get_api_key():
        try:
            return _roll_forward(_parse_with_ai(text)), "ai"
        except Exception as e:  # network down, bad key, bad JSON ... -> still works
            print(f"[ai] falling back to offline parser: {e}")
    return _roll_forward(_fallback_parse(text)), "offline"


def parse_task_from_text(text: str) -> Task:  # backwards compatible name
    return parse_task(text)[0]


def _parse_with_ai(text: str) -> Task:
    now = datetime.now()
    system_prompt = f"""You convert a spoken or typed task request (English, Hindi or Hinglish) into JSON.
Now: {now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%A')}).
Resolve relative dates/times ("tomorrow", "kal", "parso", "next Monday", "shaam 6 baje") to real values.
Reply with ONLY one JSON object, no markdown:
{{
  "title": "short clean title without date/time words",
  "description": "",
  "due_date": "YYYY-MM-DD or null",
  "due_time": "HH:MM 24h or null",
  "priority": "Low|Medium|High",
  "category": "General|Work|Personal|Health|Study",
  "recurrence": "None|Daily|Weekdays|Weekly|Monthly",
  "remind_before": 0
}}
recurrence only if the user says repeat words (daily, every Monday, roz, har hafte). remind_before is minutes (0 if not asked).
If priority/category are not mentioned, use best judgment."""
    resp = _get_client().messages.create(
        model=config.get_setting("model"), max_tokens=300, system=system_prompt,
        messages=[{"role": "user", "content": text}],
    )
    return _task_from_dict(_extract_json(resp.content[0].text), text)


def _task_from_dict(data: dict, original: str) -> Task:
    due_date = data.get("due_date")
    try:
        date.fromisoformat(due_date) if due_date else None
    except (TypeError, ValueError):
        due_date = None
    due_time = data.get("due_time")
    try:
        datetime.strptime(due_time, "%H:%M") if due_time else None
    except (TypeError, ValueError):
        due_time = None
    prio = data.get("priority") if data.get("priority") in PRIORITIES else "Medium"
    cat = data.get("category") if data.get("category") in CATEGORIES else "General"
    rec = data.get("recurrence") if data.get("recurrence") in RECURRENCES else "None"
    try:
        rb = max(0, int(data.get("remind_before") or 0))
    except (TypeError, ValueError):
        rb = 0
    if rb == 0 and due_time:
        rb = int(config.get_setting("default_remind_before") or 0)
    if rec != "None" and not due_date:
        due_date = date.today().isoformat()
    return Task(title=(data.get("title") or original[:60]).strip(),
                description=data.get("description") or "", due_date=due_date,
                due_time=due_time, priority=prio, category=cat,
                recurrence=rec, remind_before=rb)


# ---------------- offline parser (no internet / no API key) ---------------- #
_WEEKDAYS = {"monday": 0, "mon": 0, "tuesday": 1, "tue": 1, "wednesday": 2, "wed": 2,
             "thursday": 3, "thu": 3, "friday": 4, "fri": 4, "saturday": 5, "sat": 5,
             "sunday": 6, "sun": 6}
_CAT_WORDS = {
    "Health": r"gym|workout|run|yoga|medicine|doctor|dentist|water|walk|dawai|exercise",
    "Work": r"meeting|office|report|client|email|mail|project|deploy|standup|invoice|deadline",
    "Study": r"study|exam|assignment|homework|revise|lecture|class|course|padhai|read",
    "Personal": r"mom|mummy|dad|papa|call|birthday|buy|shopping|family|friend|bill|recharge",
}


def _fallback_parse(text: str) -> Task:
    t = text.lower()
    today = date.today()
    due = None
    spans = []

    def grab(pattern):
        m = re.search(pattern, t)
        if m:
            spans.append(m.group(0))
        return m

    if grab(r"\b(day after tomorrow|parso)\b"):
        due = today + timedelta(days=2)
    elif grab(r"\b(tomorrow|tmrw|kal)\b"):
        due = today + timedelta(days=1)
    elif grab(r"\b(today|aaj)\b"):
        due = today
    else:
        m = grab(r"\b(?:next\s+|on\s+)?(monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|saturday|sat|sunday|sun)\b")
        if m:
            wd = _WEEKDAYS[m.group(1)]
            due = today + timedelta(days=(wd - today.weekday()) % 7 or 7)

    hh = mm = None
    m = grab(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b")
    if m:
        hh, mm = int(m.group(1)), int(m.group(2) or 0)
        hh = hh % 12 + (12 if m.group(3) == "pm" else 0)
    else:
        m = grab(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(?:baje|bje|o'?clock)\b")
        if m:
            hh, mm = int(m.group(1)), int(m.group(2) or 0)
            if re.search(r"shaam|evening|raat|night|dopahar|afternoon", t) and hh < 12:
                hh += 12
            elif re.search(r"subah|morning", t) and hh == 12:
                hh = 0
        else:
            m = grab(r"\bat\s+(\d{1,2}):(\d{2})\b")
            if m:
                hh, mm = int(m.group(1)), int(m.group(2))
    for w in re.findall(r"\b(?:subah|morning|shaam|evening|raat|night|dopahar|afternoon)\b", t):
        spans.append(w)
    due_time = f"{hh:02d}:{mm:02d}" if hh is not None and 0 <= hh < 24 and 0 <= mm < 60 else None

    prio = "Medium"
    if grab(r"[,.]?\s*\b(high priority|urgent|important|zaroori|asap)\b"):
        prio = "High"
    elif grab(r"[,.]?\s*\b(low priority|whenever|no rush)\b"):
        prio = "Low"

    rec = "None"
    if grab(r"\b(every day|everyday|daily|roz|rozana|har din)\b"):
        rec = "Daily"
    elif grab(r"\b(every week|weekly|har hafte)\b"):
        rec = "Weekly"
    elif grab(r"\b(every weekday|weekdays)\b"):
        rec = "Weekdays"
    elif grab(r"\b(every month|monthly|har mahine)\b"):
        rec = "Monthly"
    if rec != "None" and not due:
        due = today

    category = "General"
    for cat, pat in _CAT_WORDS.items():
        if re.search(rf"\b({pat})\b", t):
            category = cat
            break

    title = text
    for s in spans:
        title = re.sub(re.escape(s), " ", title, count=1, flags=re.I)
    title = re.sub(r"^\s*(please\s+)?(remind me to|remind me|add (a )?(task|reminder)( to)?|mujhe)\s+", "", title, flags=re.I)
    title = re.sub(r"\b(at|on|by|ko)\s*$", "", title.strip(" ,.-"), flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" ,.-") or text.strip()
    title = title[:1].upper() + title[1:]

    rb = int(config.get_setting("default_remind_before") or 0) if due_time else 0
    return Task(title=title[:90], due_date=due.isoformat() if due else None, due_time=due_time,
                priority=prio, category=category, recurrence=rec, remind_before=rb)


# ---------------------------------------------------------------------- #
# 2. Habit-based suggestions
# ---------------------------------------------------------------------- #
def suggest_tasks_from_history(history: list, max_suggestions: int = 3) -> list:
    if len(history) < 3:
        return []
    summary = [{
        "title": t.title, "category": t.category, "status": t.status,
        "day_of_week": _day_of_week(t.due_date) or _day_of_week(t.created_at),
        "time": t.due_time, "recurrence": t.recurrence,
    } for t in history]
    today = date.today()
    system_prompt = f"""You analyze a user's task history to find repeating habits/routines
(same task/category on the same weekday or time) and suggest up to {max_suggestions} tasks they likely want soon.
Today is {today.isoformat()} ({today.strftime('%A')}). Don't suggest tasks that are already Pending.
Reply with ONLY a JSON array, each item:
{{"title": "...", "reason": "short reason", "suggested_date": "YYYY-MM-DD or null", "suggested_time": "HH:MM or null"}}
If there is no clear pattern reply []."""
    try:
        resp = _get_client().messages.create(
            model=config.get_setting("model"), max_tokens=500, system=system_prompt,
            messages=[{"role": "user", "content": json.dumps(summary)}],
        )
        out = _extract_json(resp.content[0].text)
    except AIAssistantError:
        raise
    except Exception as e:
        raise AIAssistantError(f"AI request failed: {e}")
    return out if isinstance(out, list) else []


def test_connection():
    """Returns (ok, message) - used by the Settings screen."""
    try:
        r = _get_client().messages.create(
            model=config.get_setting("model"), max_tokens=10,
            messages=[{"role": "user", "content": "Reply with: ok"}])
        return True, "Connected ✓"
    except Exception as e:
        return False, str(e)[:160]


def _day_of_week(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.split("T")[0]).strftime("%A")
    except ValueError:
        return None


# ---------------------------------------------------------------------- #
# 3. Daily briefing (local, no API)
# ---------------------------------------------------------------------- #
def build_briefing(tasks: list) -> str:
    now = datetime.now()
    greet = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 17 else "Good evening"
    if not tasks:
        return f"{greet}. Nothing pending for today. Enjoy your free time!"
    overdue = [t for t in tasks if t.is_overdue(now)]
    rank = {"High": 0, "Medium": 1, "Low": 2}
    top = sorted(tasks, key=lambda t: (t.due_time or "99:99", rank.get(t.priority, 1)))[:3]
    parts = [f"{greet}. You have {len(tasks)} task{'s' if len(tasks) != 1 else ''} for today."]
    if overdue:
        parts.append(f"{len(overdue)} {'is' if len(overdue) == 1 else 'are'} overdue.")
    nxt = []
    for t in top:
        nxt.append(f"{t.title} at {t.due_time}" if t.due_time else t.title)
    parts.append("Up next: " + ", ".join(nxt) + ".")
    return " ".join(parts)
