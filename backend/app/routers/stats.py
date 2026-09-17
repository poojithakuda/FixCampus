"""
FixCampus — Stats & analytics
"""

from fastapi import APIRouter, Depends
from ..deps import get_db, require_roles
from ..utils import sla_breached

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def overview(db=Depends(get_db)):
    resolved = db.execute(
        "SELECT COUNT(*) as c FROM tickets WHERE status IN ('resolved', 'closed')"
    ).fetchone()["c"]
    users = db.execute("SELECT COUNT(*) as c FROM users WHERE status = 'active'").fetchone()["c"]

    avg_row = db.execute(
        """SELECT AVG((julianday(resolved_at) - julianday(created_at)) * 24) as avg_hours
           FROM tickets WHERE resolved_at IS NOT NULL"""
    ).fetchone()
    avg_hours = avg_row["avg_hours"]
    avg_response_time = f"{max(1, round(avg_hours))}h" if avg_hours else "—"

    return {"resolved": resolved, "users": users, "avgResponseTime": avg_response_time}


@router.get("/departments")
def department_breakdown(db=Depends(get_db), admin: dict = Depends(require_roles("admin"))):
    rows = db.execute(
        """SELECT d.id, d.name, d.category,
                  COUNT(t.id) as total,
                  SUM(CASE WHEN t.status IN ('resolved','closed') THEN 1 ELSE 0 END) as resolved,
                  SUM(CASE WHEN t.status NOT IN ('resolved','closed') THEN 1 ELSE 0 END) as open
           FROM departments d
           LEFT JOIN tickets t ON t.department_id = d.id
           GROUP BY d.id
           ORDER BY d.id"""
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["total"] = d["total"] or 0
        d["resolved"] = d["resolved"] or 0
        d["open"] = d["open"] or 0
        result.append(d)
    return result


@router.get("/hotspots")
def hotspots(db=Depends(get_db), admin: dict = Depends(require_roles("admin"))):
    rows = db.execute(
        """SELECT location, category, COUNT(*) as count
           FROM tickets
           GROUP BY location, category
           HAVING count > 1
           ORDER BY count DESC
           LIMIT 10"""
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/sla-breaches")
def sla_breaches_route(db=Depends(get_db), admin: dict = Depends(require_roles("admin"))):
    open_tickets = db.execute("SELECT * FROM tickets WHERE status NOT IN ('resolved', 'closed')").fetchall()
    return [dict(t) for t in open_tickets if sla_breached(t)]
