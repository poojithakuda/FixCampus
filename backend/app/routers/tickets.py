"""
FixCampus — Tickets (complaint) routes
Implements the three modules from the project brief:
  Module 1 — Issue Reporting
  Module 2 — Categorisation & Routing (priority + duplicate detection)
  Module 3 — Tracking, Notification & Resolution
"""

import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from ..deps import get_db, get_current_user, require_roles
from ..schemas import TicketCreateRequest, StatusUpdateRequest, AssignRequest, ConfirmRequest
from ..utils import score_priority, find_duplicate, generate_ticket_code, sla_breached

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

VALID_STATUSES = ["reported", "acknowledged", "in_progress", "resolved", "closed"]


def with_computed(row) -> dict:
    d = dict(row)
    d["sla_breached"] = sla_breached(row)
    return d


def log_history(db, ticket_id, status, note, changed_by):
    db.execute(
        "INSERT INTO ticket_history (ticket_id, status, note, changed_by) VALUES (?, ?, ?, ?)",
        (ticket_id, status, note, changed_by),
    )


# ---------------------------------------------------------
# POST /api/tickets — Module 1 (report) + Module 2 (route/score)
# ---------------------------------------------------------
@router.post("")
def create_ticket(body: TicketCreateRequest, db=Depends(get_db), user: dict = Depends(get_current_user)):
    department = db.execute("SELECT * FROM departments WHERE category = ?", (body.category,)).fetchone()
    if not department:
        raise HTTPException(status_code=400, detail="Unknown category.")

    priority, matched_keyword = score_priority(body.description, department["default_priority"])
    duplicate = find_duplicate(db, body.category, body.location)
    ticket_code = generate_ticket_code(db)
    final_title = body.title.strip() if body.title and body.title.strip() else f"{department['name']} issue at {body.location}"

    cur = db.execute(
        """INSERT INTO tickets
           (ticket_code, title, description, category, location, department_id, priority, status, created_by, duplicate_of)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'reported', ?, ?)""",
        (
            ticket_code, final_title, body.description, body.category, body.location,
            department["id"], priority, user["id"], duplicate["id"] if duplicate else None,
        ),
    )
    ticket_id = cur.lastrowid

    if duplicate:
        note = f"Reported. Matched as a possible duplicate of {duplicate['ticket_code']} at the same location."
    elif matched_keyword:
        note = f'Reported. Priority escalated to High (matched keyword: "{matched_keyword}").'
    else:
        note = "Reported."
    log_history(db, ticket_id, "reported", note, user["id"])
    db.commit()

    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    result = with_computed(ticket)
    result["department"] = department["name"]
    result["duplicate_of_code"] = duplicate["ticket_code"] if duplicate else None
    return result


# ---------------------------------------------------------
# POST /api/tickets/{id}/photo — optional photo attachment
# ---------------------------------------------------------
@router.post("/{ticket_id}/photo")
def upload_photo(ticket_id: int, file: UploadFile = File(...), db=Depends(get_db), user: dict = Depends(get_current_user)):
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if ticket["created_by"] != user["id"] and user["role"] not in ("admin",):
        raise HTTPException(status_code=403, detail="Only the reporter or an admin can attach a photo.")

    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{ticket_id}-{os.urandom(4).hex()}{ext}"
    dest = UPLOAD_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    photo_path = f"/uploads/{filename}"
    db.execute("UPDATE tickets SET photo_path = ?, updated_at = datetime('now') WHERE id = ?", (photo_path, ticket_id))
    db.commit()
    return {"photo_path": photo_path}


# ---------------------------------------------------------
# GET /api/tickets — role-scoped list
# ---------------------------------------------------------
@router.get("")
def list_tickets(
    status: str = None,
    category: str = None,
    priority: str = None,
    scope: str = None,
    db=Depends(get_db),
    user: dict = Depends(get_current_user),
):
    clauses, params = [], []

    if user["role"] == "student":
        clauses.append("created_by = ?")
        params.append(user["id"])
    elif user["role"] == "staff":
        if scope == "assigned":
            clauses.append("assigned_to = ?")
            params.append(user["id"])
        else:
            clauses.append("department_id = ?")
            params.append(user["department_id"])
    # admin: no forced clause

    if status:
        clauses.append("status = ?")
        params.append(status)
    if category:
        clauses.append("category = ?")
        params.append(category)
    if priority:
        clauses.append("priority = ?")
        params.append(priority)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(f"SELECT * FROM tickets {where} ORDER BY created_at DESC", params).fetchall()
    return [with_computed(r) for r in rows]


# ---------------------------------------------------------
# GET /api/tickets/{id} — detail + status history
# ---------------------------------------------------------
@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db=Depends(get_db), user: dict = Depends(get_current_user)):
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    can_view = (
        user["role"] == "admin"
        or (user["role"] == "student" and ticket["created_by"] == user["id"])
        or (user["role"] == "staff" and ticket["department_id"] == user["department_id"])
    )
    if not can_view:
        raise HTTPException(status_code=403, detail="You don't have access to this ticket.")

    history = db.execute(
        "SELECT * FROM ticket_history WHERE ticket_id = ? ORDER BY changed_at ASC", (ticket_id,)
    ).fetchall()

    result = with_computed(ticket)
    result["history"] = [dict(h) for h in history]
    return result


# ---------------------------------------------------------
# PATCH /api/tickets/{id}/status — Module 3 (staff progresses the ticket)
# ---------------------------------------------------------
@router.patch("/{ticket_id}/status")
def update_status(
    ticket_id: int, body: StatusUpdateRequest, db=Depends(get_db), user: dict = Depends(require_roles("staff", "admin"))
):
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if user["role"] == "staff" and ticket["department_id"] != user["department_id"]:
        raise HTTPException(status_code=403, detail="This ticket belongs to a different department.")

    if body.status == "resolved":
        db.execute(
            "UPDATE tickets SET status = ?, resolved_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
            (body.status, ticket_id),
        )
    else:
        db.execute(
            "UPDATE tickets SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (body.status, ticket_id),
        )

    log_history(db, ticket_id, body.status, body.note, user["id"])
    db.commit()

    updated = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return with_computed(updated)


# ---------------------------------------------------------
# PATCH /api/tickets/{id}/assign — admin assigns to a staff member
# ---------------------------------------------------------
@router.patch("/{ticket_id}/assign")
def assign_ticket(ticket_id: int, body: AssignRequest, db=Depends(get_db), user: dict = Depends(require_roles("admin"))):
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    staff_member = db.execute(
        "SELECT * FROM users WHERE id = ? AND role = 'staff' AND status = 'active'", (body.assigned_to,)
    ).fetchone()
    if not staff_member:
        raise HTTPException(status_code=400, detail="Not an active staff account.")
    if staff_member["department_id"] != ticket["department_id"]:
        raise HTTPException(status_code=400, detail="Staff member is not in this ticket's department.")

    next_status = "acknowledged" if ticket["status"] == "reported" else ticket["status"]
    db.execute(
        "UPDATE tickets SET assigned_to = ?, status = ?, updated_at = datetime('now') WHERE id = ?",
        (staff_member["id"], next_status, ticket_id),
    )
    log_history(db, ticket_id, next_status, f"Assigned to {staff_member['name']}.", user["id"])
    db.commit()

    updated = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return with_computed(updated)


# ---------------------------------------------------------
# POST /api/tickets/{id}/confirm — Module 3 (reporter confirms or reopens)
# ---------------------------------------------------------
@router.post("/{ticket_id}/confirm")
def confirm_ticket(ticket_id: int, body: ConfirmRequest, db=Depends(get_db), user: dict = Depends(get_current_user)):
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if ticket["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the reporter can confirm this ticket.")
    if ticket["status"] != "resolved":
        raise HTTPException(status_code=400, detail="Only a resolved ticket can be confirmed or reopened.")

    if body.confirmed:
        db.execute(
            "UPDATE tickets SET status = 'closed', closed_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
            (ticket_id,),
        )
        log_history(db, ticket_id, "closed", "Reporter confirmed the fix.", user["id"])
        if body.rating:
            db.execute(
                "INSERT INTO feedback (ticket_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
                (ticket_id, user["id"], body.rating, body.comment),
            )
    else:
        db.execute(
            "UPDATE tickets SET status = 'in_progress', updated_at = datetime('now') WHERE id = ?", (ticket_id,)
        )
        log_history(db, ticket_id, "in_progress", "Reporter marked the issue as unresolved — reopened.", user["id"])

    db.commit()
    updated = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return with_computed(updated)
