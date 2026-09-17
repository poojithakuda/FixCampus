# FixCampus backend setup — Windows PowerShell
# Run this from inside the backend/ folder:
#   .\setup.ps1
#
# If PowerShell blocks the script with a red "execution policy" error, run
# this once first, then try again:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Write-Host "Creating virtual environment..." -ForegroundColor Cyan
python -m venv venv

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
}

Write-Host ""
Write-Host "Setup complete. Starting the server on http://localhost:8000 ..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop. Leave this window open while you use the app." -ForegroundColor Green
Write-Host ""
uvicorn app.main:app --reload --port 8000
