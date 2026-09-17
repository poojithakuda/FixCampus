"""
FixCampus — Departments
"""

from fastapi import APIRouter, Depends
from ..deps import get_db

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("")
def list_departments(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM departments ORDER BY id").fetchall()
    return [dict(r) for r in rows]
