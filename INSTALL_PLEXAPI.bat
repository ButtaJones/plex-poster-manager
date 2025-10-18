@echo off
echo Installing PlexAPI into your venv...
echo.

REM Direct path to pip in your venv
C:\Plex\plex-poster-manager-main\backend\venv\Scripts\pip.exe install PlexAPI==4.15.16

echo.
echo Done! Now close the launcher and restart it.
pause
