@echo off
REM Plex Poster Manager v2.0 - Windows Setup Script
REM This reinstalls backend dependencies including PlexAPI

echo =========================================================
echo  Plex Poster Manager v2.0 - Windows Setup
echo =========================================================
echo.
echo This will reinstall backend dependencies for v2.0
echo (Includes new PlexAPI library requirement)
echo.
pause

cd backend

echo.
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/2] Installing/upgrading dependencies from requirements.txt...
echo (This includes PlexAPI==4.15.16)
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo =========================================================
echo  Setup Complete!
echo =========================================================
echo.
echo Next steps:
echo 1. Get your Plex token from:
echo    https://support.plex.tv/articles/204059436
echo.
echo 2. Run: python launcher_gui.py
echo.
echo 3. Enter your Plex Server URL (usually http://localhost:32400)
echo.
echo 4. Enter your Plex Token (REQUIRED for v2.0!)
echo.
echo 5. Click "Save Configuration"
echo.
echo 6. Click "Launch Servers"
echo.
echo =========================================================
pause
