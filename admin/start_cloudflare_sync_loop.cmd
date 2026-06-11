@echo off
title WorldCup2026 Cloudflare Growth Sync Loop
cd /d "J:\promotion helper"

:loop
echo [%date% %time%] Syncing Cloudflare growth data...
python "admin\sync_cloudflare.py"
echo [%date% %time%] Next sync in 3 hours. Keep this window open.
timeout /t 10800 /nobreak
goto loop
