@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 ( set "PY=py" ) else ( set "PY=python" )

rem Mevcut acik Windows Terminal pencerenizin hemen yanina (Dikey Bolunmus Panel / Split Pane) olarak acar!
wt.exe -w 0 sp -V -d "%CD%" %PY% main.py

endlocal
