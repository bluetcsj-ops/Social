@echo off
cd /d "D:\Social-main"
start "WorldCup2026 Growth Dashboard Server" cmd /k "admin\start_growth_dashboard.cmd"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8787/admin/growth-dashboard.html"
