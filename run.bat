@echo off
rem GraviTUI baslatici. Kullanim: run.bat [1-4|test]   (bosluklu yollara dayanikli)
setlocal
chcp 65001 >nul
rem %~dp0 sonundaki ters bolu tirnagi kacirmasin diye pushd ile klasore girilir
pushd "%~dp0" || exit /b 1

set "CHOICE=%~1"
if "%CHOICE%"=="" (
  echo.
  echo   GraviTUI - ornek sec:
  echo     1  Hello Ratatui
  echo     2  3D Polyhedron
  echo     3  Dashboard
  echo     4  Office Mini
  echo     t  Testler
  echo.
  set /p "CHOICE=  Secim [1-4/t]: "
)

set "PY=py -3"
where py >nul 2>nul || set "PY=python"

if /i "%CHOICE%"=="t"    ( %PY% -m unittest discover -s tests -t . & goto :done )
if /i "%CHOICE%"=="test" ( %PY% -m unittest discover -s tests -t . & goto :done )

set "SCRIPT="
if "%CHOICE%"=="1" set "SCRIPT=examples\01_hello_ratatui.py"
if "%CHOICE%"=="2" set "SCRIPT=examples\02_3d_polyhedron.py"
if "%CHOICE%"=="3" set "SCRIPT=examples\03_dashboard.py"
if "%CHOICE%"=="4" set "SCRIPT=examples\04_office_mini.py"
if not defined SCRIPT ( echo Gecersiz secim: %CHOICE% & popd & exit /b 2 )

rem Windows Terminal varsa orada ac (-d: calisma klasoru), yoksa mevcut konsolda calistir
where wt >nul 2>nul
if %errorlevel%==0 if not defined WT_SESSION (
  start "" wt -d "%CD%" cmd /c "%PY% %SCRIPT%"
  goto :done
)
%PY% "%SCRIPT%"

:done
popd
endlocal
