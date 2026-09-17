"""
FixCampus — Auth routes
"""

from fastapi import APIRouter, Depends, HTTPException
from ..database import get_connection
from ..deps import get_db
from ..security import hash_password, verify_password, create_access_token
from ..schemas import RegisterRequest, LoginRequest, TokenResponse, PendingResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(body: RegisterRequest, db=Depends(get_db)):
    existing = db.execute("SELECT id FROM users WHERE email = ?", (body.email,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    if body.role == "staff":
        if not body.department_id:
            raise HTTPException(status_code=400, detail="Staff registration requires a department_id.")
        dept = db.execute("SELECT id FROM departments WHERE id = ?", (body.department_id,)).fetchone()
        if not dept:
            raise HTTPException(status_code=400, detail="Unknown department_id.")

    status = "pending" if body.role == "staff" else "active"
    dept_id = body.department_id if body.role == "staff" else None

    cur = db.execute(
        "INSERT INTO users (name, email, password, role, department_id, status) VALUES (?, ?, ?, ?, ?, ?)",
        (body.name, body.email, hash_password(body.password), body.role, dept_id, status),
    )
    db.commit()
    user_id = cur.lastrowid

    if body.role == "staff":
        return PendingResponse(message="Account created. It will be usable once an admin approves it.")

    user_row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    token = create_access_token(user_row)
    return TokenResponse(token=token, role=body.role, name=body.name, id=user_id, department_id=None)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db=Depends(get_db)):
    user = db.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email, password or role.")
    if body.role and user["role"] != body.role:
        raise HTTPException(status_code=401, detail="Invalid email, password or role.")
    if user["role"] == "staff" and user["status"] == "pending":
        raise HTTPException(
            status_code=403,
            detail="Your staff account is pending admin approval. You'll be able to log in once an admin approves it.",
        )
    if user["status"] == "rejected":
        raise HTTPException(status_code=403, detail="This account's registration request was rejected.")

    token = create_access_token(user)
    return TokenResponse(
        token=token, role=user["role"], name=user["name"], id=user["id"], department_id=user["department_id"]
    )
