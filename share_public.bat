@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d %~dp0

echo === Job Scraper: Public Share (Cloudflare Tunnel) ===

REM Ensure Python venv exists
if not exist .venv\Scripts\python.exe (
  echo [ERROR] Python venv not found at .venv\Scripts\python.exe
  echo Create one first (see INSTALLATION.md) and re-run this script.
  pause
  exit /b 1
)

REM Download cloudflared if missing (no account needed for ephemeral tunnel)
if not exist cloudflared.exe (
  echo Downloading cloudflared.exe ...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe' -UseBasicParsing"
  if errorlevel 1 (
    echo [ERROR] Failed to download cloudflared.exe
    echo Trying fallback downloader (certutil)...
    certutil -urlcache -split -f "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" cloudflared.exe
    if errorlevel 1 (
      echo [ERROR] Fallback download also failed.
      pause
      exit /b 1
    )
  )
)

REM Start Flask app in a new window
echo Starting Flask app on http://127.0.0.1:5000 ...
start "JobScraper Flask" .venv\Scripts\python.exe app.py

echo Waiting for server to boot...
timeout /t 5 /nobreak >nul

echo Local access available at: http://127.0.0.1:5000
echo (If your browser doesn't open automatically, copy the URL above.)

echo Starting Cloudflare Tunnel (ephemeral, free)...
echo You will get a public URL like https://^<random^>.trycloudflare.com
cloudflared.exe tunnel --url http://localhost:5000 --no-autoupdate

echo Tunnel stopped. Press any key to exit.
pause
