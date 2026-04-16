@echo off
title Auto IT News Mailer
cd /d "%~dp0"

:: Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Launch the GUI app
python app.py

:: If there's an error, pause so user can read it
if errorlevel 1 (
    echo.
    echo ERROR: Something went wrong. See message above.
    pause
)
