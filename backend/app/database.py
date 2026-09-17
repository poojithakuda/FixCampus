"""
FixCampus — Database layer (SQLite, plain SQL via Python's sqlite3)

A single embedded SQL database file. No external DB server needed.
Seeds the 5 departments and exactly two fixed admin accounts on
first run — nothing else. Every other record (students, staff,
tickets, feedback) is created for real through the API.
"""

import sqlite3
import os
from pathlib import Path
from passlib.context import CryptContext

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "database" / "fixcampus.db"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_connection():
    """New connection per call — sqlite3 connections aren't thread-safe
    to share across FastAPI's request threads."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL UNIQUE,
    default_priority TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','staff','admin')),
    department_id INTEGER REFERENCES departments(id),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','pending','rejected')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    photo_path TEXT,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    priority TEXT NOT NULL CHECK(priority IN ('Low','Medium','High')),
    status TEXT NOT NULL DEFAULT 'reported' CHECK(status IN ('reported','acknowledged','in_progress','resolved','closed')),
    created_by INTEGER NOT NULL REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    duplicate_of INTEGER REFERENCES tickets(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS ticket_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    status TEXT NOT NULL,
    note TEXT,
    changed_by INTEGER REFERENCES users(id),
    changed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER REFERENCES tickets(id),
    user_id INTEGER REFERENCES users(id),
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_department ON tickets(department_id);
CREATE INDEX IF NOT EXISTS idx_tickets_created_by ON tickets(created_by);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to);
"""

DEPARTMENTS = [
    ("Classroom Support", "classroom", "Medium", "Broken desks/chairs, faulty projectors, lighting, fans/AC."),
    ("Lab Support", "lab", "High", "Faulty equipment, computer issues, broken lab furniture."),
    ("IT / Network Department", "network", "Medium", "Wi-Fi down, slow internet, connectivity issues."),
    ("Housekeeping", "cleanliness", "Low", "Washroom hygiene, waste disposal, corridor cleanliness."),
    ("Facility & Civil Admin", "facility", "High", "Water supply, electrical faults, building maintenance."),
]

ADMINS = [
    ("Admin One", "admin1@fixcampus.edu", "admin123"),
    ("Admin Two", "admin2@fixcampus.edu", "admin123"),
]


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA)

    for name, category, priority, description in DEPARTMENTS:
        conn.execute(
            "INSERT OR IGNORE INTO departments (name, category, default_priority, description) VALUES (?, ?, ?, ?)",
            (name, category, priority, description),
        )

    for name, email, password in ADMINS:
        conn.execute(
            "INSERT OR IGNORE INTO users (name, email, password, role, status) VALUES (?, ?, ?, 'admin', 'active')",
            (name, email, pwd_context.hash(password)),
        )

    conn.commit()
    conn.close()
