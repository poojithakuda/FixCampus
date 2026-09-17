"""
FixCampus — FastAPI application entry point
Centralised Campus Problem Reporting Platform (5-department routing)
"""

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import auth, departments, tickets, users, feedback, stats

app = FastAPI(title="FixCampus API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables + seed departments/admins on startup
init_db()

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/api/health")
def health():
    return {"ok": True, "service": "fixcampus-backend"}


app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(feedback.router)
app.include_router(stats.router)


@app.exception_handler(HTTPException)
def http_exception_handler(request, exc: HTTPException):
    # Normalise FastAPI's default {"detail": ...} to {"message": ...}
    # so it matches what the frontend's error handling expects.
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc: RequestValidationError):
    first = exc.errors()[0]
    field = ".".join(str(p) for p in first["loc"] if p != "body")
    return JSONResponse(status_code=422, content={"message": f"{field}: {first['msg']}"})
