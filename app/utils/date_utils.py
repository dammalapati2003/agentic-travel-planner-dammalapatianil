from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import zoneinfo

def _get_tz(tz_name: str):
    """
    Returns a ZoneInfo timezone if available; otherwise:
    - If IST requested, returns fixed-offset IST (+05:30).
    - Else falls back to UTC.
    """
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except Exception:
        if tz_name in ("Asia/Kolkata", "Asia/Calcutta"):
            return timezone(timedelta(hours=5, minutes=30), name="IST")
        return timezone.utc

def resolve_dates(text: str, today=None, tz_name="Asia/Kolkata", default_days=2):
    tz = _get_tz(tz_name)
    now = today.astimezone(tz) if today else datetime.now(tz)
    text_lower = (text or "").lower()

    if "today" in text_lower:
        start = now.date()
    elif "tomorrow" in text_lower:
        start = (now + timedelta(days=1)).date()
    elif "next week" in text_lower:
        dow = now.weekday()  # Monday=0
        days_until_mon = (7 - dow) % 7
        if days_until_mon == 0:
            days_until_mon = 7
        start = (now + timedelta(days=days_until_mon)).date()
    else:
        start = now.date()

    end = start + timedelta(days=default_days - 1)
    return start.isoformat(), end.isoformat()
