# -*- coding: utf-8 -*-
import datetime as dt


DISPLAY_DATE_FORMAT = "%d-%m-%Y"
ISO_DATE_FORMAT = "%Y-%m-%d"


def parse_date_to_iso(value, default_today=False):
    """Return YYYY-MM-DD for storage/querying while accepting common UI formats."""
    if value is None:
        return dt.date.today().strftime(ISO_DATE_FORMAT) if default_today else ""
    if isinstance(value, dt.datetime):
        return value.strftime(ISO_DATE_FORMAT)
    if isinstance(value, dt.date):
        return value.strftime(ISO_DATE_FORMAT)

    raw = str(value).strip()
    if not raw:
        return dt.date.today().strftime(ISO_DATE_FORMAT) if default_today else ""

    raw_date = raw.split()[0]
    for fmt in (
        ISO_DATE_FORMAT,
        DISPLAY_DATE_FORMAT,
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m/%d/%Y",
    ):
        try:
            return dt.datetime.strptime(raw_date, fmt).strftime(ISO_DATE_FORMAT)
        except ValueError:
            continue
    return dt.date.today().strftime(ISO_DATE_FORMAT) if default_today else raw_date


def format_date_display(value):
    iso = parse_date_to_iso(value)
    if not iso:
        return ""
    try:
        return dt.datetime.strptime(iso, ISO_DATE_FORMAT).strftime(DISPLAY_DATE_FORMAT)
    except ValueError:
        return str(value or "")


def format_datetime_display(value):
    if not value:
        return ""
    raw = str(value).strip()
    try:
        parsed = dt.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        return parsed.strftime(f"{DISPLAY_DATE_FORMAT} %H:%M:%S")
    except ValueError:
        if " " in raw:
            date_part, time_part = raw.split(" ", 1)
            return f"{format_date_display(date_part)} {time_part}".strip()
        return format_date_display(raw)
