# FixCampus — Centralised Campus Problem Reporting Platform

Report a campus issue, watch it get auto-routed to the right department by
priority, and track it through to resolution.

```
FixCampus/
├── frontend/     HTML + CSS + vanilla JavaScript
└── backend/      Python + FastAPI + SQLite (SQL database, JSON API)
```

## Quick start

**1. Backend**

The easiest way: run the setup script for your OS from inside `backend/`.
It creates the virtual environment, installs dependencies, creates `.env`,
and starts the server — all in one step.

Windows (PowerShell):
```powershell
cd backend
.\setup.ps1
```
If PowerShell blocks the script with a red "execution policy" error, run
this once, then try again:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

macOS / Linux:
```bash
cd backend
bash setup.sh
```

Prefer to run the commands yourself instead of the script? See
`backend/README.md` — it has the exact one-per-line commands for both
PowerShell and bash (don't mix them: `&&` and `source` are bash syntax and
will fail in PowerShell).

**2. Frontend** — just open `frontend/index.html` in a browser (or serve the
folder with any static file server). It talks to the backend at
`http://localhost:8000/api`.

## What's inside

- **5 departments**, auto-routed by category: Classroom Support, Lab
  Support, IT / Network, Housekeeping, Facility & Civil Admin
- **Priority scoring** — urgent keywords in a description (e.g. "gas leak",
  "exposed wire") escalate a ticket to High priority automatically
- **Duplicate detection** — a new report at the same location/category as
  an unresolved one is flagged and linked instead of creating noise
- **Role-based accounts** — students register and log in immediately; staff
  register against a department and need admin approval; only 2 fixed admin
  accounts exist (no admin self-registration)
- **Full status lifecycle** — reported → acknowledged → in progress →
  resolved → closed, with the reporter having final say on closing or
  reopening
- **SLA tracking** and a department-by-department breakdown for admins
- No fake data anywhere — a fresh install has just the 5 departments and 2
  admin logins. Everything else is real data you create.

See `backend/README.md` for the full API reference and `frontend/` for the
page-by-page breakdown.

## Admin accounts (only these two exist)

| Email | Password |
|---|---|
| `admin1@fixcampus.edu` | `admin123` |
| `admin2@fixcampus.edu` | `admin123` |

Change these before any real deployment.
