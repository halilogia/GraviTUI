@echo off
setlocal
cd /d "%~dp0"

rem Check if python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [HATA] Python bulunamadi! Lutfen Python 3 yukleyin veya PATH'e ekleyin.
        pause
        exit /b 1
    )
    set "PY=py"
) else (
    set "PY=python"
)

rem -w new: Mevcut acik baska TUI veya terminal pencerelerine karismadan
rem YEPYENI VE BAGIMSIZ ayri bir Windows Terminal penceresinde baslatir.
where wt.exe >nul 2>nul
if %errorlevel%==0 (
    start "" wt.exe -w new --size 120,36 -d "%CD%" %PY% main.py
) else (
    start "RPG Dice TUI - 24-bit TrueColor" cmd /c "%PY% main.py"
)

endlocal
