"""
FixCampus — Users (admin manages staff accounts)
"""

from fastapi import APIRouter, Depends, HTTPException
from ..deps import get_db, require_roles

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(
    role: str = None,
    status: str = None,
    department_id: int = None,
    db=Depends(get_db),
    user: dict = Depends(require_roles("admin")),
):
    clauses, params = [], []
    if role:
        clauses.append("role = ?")
        params.append(role)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if department_id:
        clauses.append("department_id = ?")
        params.append(department_id)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(
        f"SELECT id, name, email, role, department_id, status, created_at FROM users {where} ORDER BY created_at DESC",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


@router.patch("/{user_id}/approve")
def approve_staff(user_id: int, db=Depends(get_db), admin: dict = Depends(require_roles("admin"))):
    target = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target["role"] != "staff":
        raise HTTPException(status_code=400, detail="Only staff accounts go through approval.")

    db.execute("UPDATE users SET status = 'active' WHERE id = ?", (user_id,))
    db.commit()
    return {"id": user_id, "status": "active"}


@router.patch("/{user_id}/reject")
def reject_staff(user_id: int, db=Depends(get_db), admin: dict = Depends(require_roles("admin"))):
    target = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target["role"] != "staff":
        raise HTTPException(status_code=400, detail="Only staff accounts go through approval.")

    db.execute("UPDATE users SET status = 'rejected' WHERE id = ?", (user_id,))
    db.commit()
    return {"id": user_id, "status": "rejected"}
