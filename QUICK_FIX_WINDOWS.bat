@echo off
REM Quick fix to install PlexAPI on Windows

echo Installing PlexAPI...
cd backend
call venv\Scripts\activate.bat
pip install PlexAPI==4.15.16
echo.
echo Done! PlexAPI installed.
echo Now run: python launcher_gui.py
pause
