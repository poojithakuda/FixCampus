"""
FixCampus — Feedback
"""

from fastapi import APIRouter, Depends
from ..deps import get_db

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.get("")
def list_feedback(db=Depends(get_db)):
    rows = db.execute(
        """SELECT f.id, f.rating, f.comment, f.created_at, u.name as user_name
           FROM feedback f
           LEFT JOIN users u ON u.id = f.user_id
           ORDER BY f.created_at DESC
           LIMIT 20"""
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["user_name"] = d["user_name"] or "Anonymous"
        result.append(d)
    return result
