@echo off
title Claude Code Agent Tree TUI
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
mode con: cols=122 lines=39
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Application exited with code %ERRORLEVEL%.
    pause
)
