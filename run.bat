@echo off
title ARCEUS REVIEW FETCHER - AutoFetch System
color 0A
cls
echo ================================================================
echo           ARCEUS REVIEW FETCHER - AUTO-FETCH SYSTEM            
echo ================================================================
echo.

echo Checking Python requirements...
pip install -r requirements.txt --quiet --disable-pip-version-check

echo.
echo Starting Arceus Review Fetcher Server...
echo Local Dashboard: http://127.0.0.1:5000
echo.

start "" "http://127.0.0.1:5000"
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An error occurred while running the application.
    pause
)
