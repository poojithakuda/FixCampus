"""
FixCampus — Pydantic schemas (request validation + response shapes).
These are what make every API response valid, typed JSON.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["student", "staff"]
    department_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[Literal["student", "staff", "admin"]] = None


class TokenResponse(BaseModel):
    token: str
    role: str
    name: str
    id: int
    department_id: Optional[int] = None


class PendingResponse(BaseModel):
    pending: bool = True
    message: str


# ---------- Tickets ----------
class TicketCreateRequest(BaseModel):
    title: Optional[str] = None
    category: str
    location: str
    description: str


class StatusUpdateRequest(BaseModel):
    status: Literal["acknowledged", "in_progress", "resolved"]
    note: Optional[str] = None


class AssignRequest(BaseModel):
    assigned_to: int


class ConfirmRequest(BaseModel):
    confirmed: bool
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None
