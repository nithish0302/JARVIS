from datetime import UTC, datetime, timedelta

import httpx

from .google_auth import get_valid_token

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


def get_calendar_headers() -> dict:
    token = get_valid_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_todays_events() -> list[dict]:
    headers = get_calendar_headers()

    now = datetime.now(UTC)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    params = {
        "timeMin": start_of_day.isoformat(),
        "timeMax": end_of_day.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    resp = httpx.get(
        f"{CALENDAR_API_BASE}/calendars/primary/events",
        headers=headers,
        params=params,
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    events = data.get("items", [])
    results = []

    for event in events:
        results.append(
            {
                "id": event.get("id"),
                "summary": event.get("summary", "No Title"),
                "start": event.get("start", {}).get(
                    "dateTime", event.get("start", {}).get("date")
                ),
                "end": event.get("end", {}).get(
                    "dateTime", event.get("end", {}).get("date")
                ),
                "location": event.get("location", ""),
            }
        )

    return results


def get_upcoming_events(days: int = 7) -> list[dict]:
    headers = get_calendar_headers()

    now = datetime.now(UTC)
    end_time = now + timedelta(days=days)

    params = {
        "timeMin": now.isoformat(),
        "timeMax": end_time.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": 10,
    }

    resp = httpx.get(
        f"{CALENDAR_API_BASE}/calendars/primary/events",
        headers=headers,
        params=params,
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    events = data.get("items", [])
    results = []

    for event in events:
        results.append(
            {
                "id": event.get("id"),
                "summary": event.get("summary", "No Title"),
                "start": event.get("start", {}).get(
                    "dateTime", event.get("start", {}).get("date")
                ),
                "end": event.get("end", {}).get(
                    "dateTime", event.get("end", {}).get("date")
                ),
                "location": event.get("location", ""),
            }
        )

    return results


def _normalize_date(date_str: str) -> dict:
    import datetime

    from dateutil import parser

    try:
        # fuzzy=True helps ignore random words like 'on' or 'at'
        dt = parser.parse(date_str, fuzzy=True)
    except Exception as e:
        raise ValueError(f"Could not parse date: {date_str}") from e

    # Heuristic to determine if a time was provided
    has_time = any(c in date_str.lower() for c in [":", "am", "pm", "t"])

    if not has_time and dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        return {"date": dt.strftime("%Y-%m-%d")}

    # Convert to IST (+05:30) as requested
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ist)
    else:
        dt = dt.astimezone(ist)

    return {"dateTime": dt.isoformat()}


def create_event(title: str, start: str, end: str, description: str = "") -> bool:
    # NEVER called directly without confirm_action in the backend
    headers = get_calendar_headers()

    start_payload = _normalize_date(start)
    end_payload = _normalize_date(end)

    payload = {
        "summary": title,
        "description": description,
        "start": start_payload,
        "end": end_payload,
    }

    resp = httpx.post(
        f"{CALENDAR_API_BASE}/calendars/primary/events",
        headers=headers,
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()

    return True


def get_event_detail(event_id: str) -> dict:
    headers = get_calendar_headers()

    resp = httpx.get(
        f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}",
        headers=headers,
        timeout=30.0,
    )
    resp.raise_for_status()
    event = resp.json()

    return {
        "id": event.get("id"),
        "summary": event.get("summary", "No Title"),
        "start": event.get("start", {}).get(
            "dateTime", event.get("start", {}).get("date")
        ),
        "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date")),
        "location": event.get("location", ""),
        "description": event.get("description", ""),
    }
