"""
FixCampus — Categorisation & Routing helpers
Mirrors "Module 2" from the project brief:
  - scan description for urgency keywords
  - assign priority (High / Medium / Low)
  - check for a duplicate at the same location
  - route to the correct department
"""

from datetime import datetime, timedelta, timezone

HIGH_PRIORITY_KEYWORDS = [
    "no water", "wifi down", "wi-fi down", "exposed wire", "fire", "smoke",
    "spark", "sparking", "electric shock", "shock hazard", "gas leak",
    "gas smell", "flooding", "flooded", "short circuit", "no power",
    "power outage", "security threat", "safety hazard", "injury", "leak",
]

PRIORITY_RANK = {"Low": 0, "Medium": 1, "High": 2}

# SLA target, in hours, by priority — used for dashboard alerts.
SLA_HOURS = {"High": 4, "Medium": 24, "Low": 72}


def score_priority(description: str, default_priority: str):
    """Escalate to High if an urgency keyword is present. Never downgrades."""
    text = (description or "").lower()
    matched = next((kw for kw in HIGH_PRIORITY_KEYWORDS if kw in text), None)
    if matched and PRIORITY_RANK["High"] > PRIORITY_RANK[default_priority]:
        return "High", matched
    return default_priority, None


def find_duplicate(conn, category: str, location: str, within_days: int = 7):
    """An unresolved ticket, same category + same (normalised) location,
    opened within the last N days."""
    normalized_location = location.strip().lower()
    cutoff = (datetime.utcnow() - timedelta(days=within_days)).strftime("%Y-%m-%d %H:%M:%S")
    row = conn.execute(
        """SELECT * FROM tickets
           WHERE category = ?
             AND lower(trim(location)) = ?
             AND status NOT IN ('resolved', 'closed')
             AND duplicate_of IS NULL
             AND created_at >= ?
           ORDER BY created_at DESC
           LIMIT 1""",
        (category, normalized_location, cutoff),
    ).fetchone()
    return row


def generate_ticket_code(conn) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    count = conn.execute("SELECT COUNT(*) as c FROM tickets").fetchone()["c"]
    seq = str(count + 1).zfill(4)
    return f"FC-{today}-{seq}"


def sla_breached(ticket_row) -> bool:
    if ticket_row["status"] in ("resolved", "closed"):
        return False
    created = datetime.strptime(ticket_row["created_at"], "%Y-%m-%d %H:%M:%S")
    hours_open = (datetime.utcnow() - created).total_seconds() / 3600
    return hours_open > SLA_HOURS[ticket_row["priority"]]
