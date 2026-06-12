@echo off
title WorldCup2026 Growth Dashboard
cd /d "D:\Social-main"
set "PYTHON_EXE=C:\AI\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Cannot find %PYTHON_EXE%
  echo Please edit admin\start_growth_dashboard.cmd and set PYTHON_EXE to your Python path.
  pause
  exit /b 1
)

echo Starting local growth dashboard...
echo.
echo Open this page:
echo http://127.0.0.1:8787/admin/growth-dashboard.html
echo.
echo Keep this window open while using the refresh button.
echo Press Ctrl+C to stop.
echo.
"%PYTHON_EXE%" "admin\local_growth_server.py" --port 8787

echo.
echo Growth dashboard server stopped.
pause
