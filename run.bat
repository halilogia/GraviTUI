@echo off
rem GraviTUI Baslatici (Interactive Hub & CLI Launcher)
setlocal
chcp 65001 >nul
pushd "%~dp0" || exit /b 1

set "PY=py -3"
where py >nul 2>nul || set "PY=python"

rem Test calistirma kestirmesi
if /i "%~1"=="t"    ( %PY% -m unittest discover -s tests -t . & goto :done )
if /i "%~1"=="test" ( %PY% -m unittest discover -s tests -t . & goto :done )

rem Windows Terminal varsa ve henuz terminal oturumunda degilsek yeni WT sekmesinde/penceresinde ac
where wt >nul 2>nul
if %errorlevel%==0 if not defined WT_SESSION (
  start "" wt -d "%CD%" --title "GraviTUI Hub" cmd /c "%PY% run_hub.py %*"
  goto :done
)

%PY% run_hub.py %*

:done
popd
endlocal
