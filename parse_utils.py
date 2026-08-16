"""
Helpers for turning messy, free-text user input (from Telegram chat, or from
the raw Google Form data) into clean numeric values.

Handles formats seen in real responses like:
    "5k", "3000", "2k-3k", "5000-6000", "Around 3500", "11k", "800-900"
    "2 days", "3 days", "same day return", "8-10"
"""

import re
from datetime import date


def parse_budget(text):
    """
    Parse a budget string into a single numeric rupee value.
    If a range is given (e.g. "3000-4000" or "2k-3k"), returns the upper bound,
    since "budget" is treated as the ceiling the user is willing to spend.
    Returns None if no number could be found.
    """
    if text is None:
        return None

    t = str(text).lower().strip()
    t = t.replace(",", "")
    t = re.sub(r"(inr|rs\.?|rupees|around|approx\.?|₹)", "", t)

    numbers = []
    for num_str, k_suffix in re.findall(r"(\d+(?:\.\d+)?)\s*(k)?", t):
        if not num_str:
            continue
        value = float(num_str)
        if k_suffix:
            value *= 1000
        numbers.append(value)

    if not numbers:
        return None

    return max(numbers)


def parse_days(text):
    """
    Parse a trip-duration string into a single numeric day count.
    If a range is given (e.g. "8-10"), returns the upper bound, since it's
    treated as the max days the user has available.
    "same day return" (no overnight stay) is treated as 1 day.
    Returns None if no number could be found and it isn't a same-day phrase.
    """
    if text is None:
        return None

    t = str(text).lower().strip()

    if "same day" in t or "day return" in t:
        return 1.0

    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", t)]
    if not numbers:
        return None

    return max(numbers)


_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

_RANGE_RE = re.compile(
    r"(?:([a-zA-Z]+)\s+)?(\d{1,2})(?:st|nd|rd|th)?\s*[-–to]+\s*(\d{1,2})(?:st|nd|rd|th)?(?:\s+([a-zA-Z]+))?"
)

_DATE_RE = re.compile(
    r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)|([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?"
)


def _month_num(name):
    key = name.lower()
    return _MONTHS.get(key[:3]) or _MONTHS.get(key)


def _extract_dates(text, ref_year):
    # First catch "28-30 Aug" / "28 to 30 Aug" style ranges sharing one month.
    range_match = _RANGE_RE.search(text)
    if range_match:
        month1, day1, day2, month2 = range_match.groups()

        month_name = month1 or month2
        month = _month_num(month_name)
        if month is not None:
            try:
                return [
                    date(ref_year, month, int(day1)),
                    date(ref_year, month, int(day2)),
                ]
            except ValueError:
                pass

    found = []
    for m in _DATE_RE.finditer(text):
        if m.group(1) and m.group(2):
            day_str, month_name = m.group(1), m.group(2)
        else:
            month_name, day_str = m.group(3), m.group(4)
        month = _month_num(month_name)
        if month is None:
            continue
        try:
            found.append(date(ref_year, month, int(day_str)))
        except ValueError:
            continue
    return found


def parse_free_window(text, today=None):
    """
    Parse a "when are you free" answer into a start date, end date, and
    total free-day count. Handles explicit date ranges ("Aug 28 to Aug 30",
    "28-30 Aug"), a single date ("Aug 28"), or a plain day count ("3 days",
    "3") as a fallback.

    Returns {"start": date|None, "end": date|None, "free_days": int},
    or None if nothing usable could be parsed.
    """
    if today is None:
        today = date.today()

    t = str(text).strip()
    dates = _extract_dates(t, today.year)

    if len(dates) >= 2:
        start, end = sorted(dates[:2])
        if end < today:
            start = date(start.year + 1, start.month, start.day)
            end = date(end.year + 1, end.month, end.day)
        return {"start": start, "end": end, "free_days": (end - start).days + 1}

    if len(dates) == 1:
        start = dates[0]
        if start < today:
            start = date(start.year + 1, start.month, start.day)
        return {"start": start, "end": start, "free_days": 1}

    days = parse_days(t)
    if days is not None:
        return {"start": None, "end": None, "free_days": int(days)}

    return None
