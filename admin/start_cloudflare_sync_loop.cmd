@echo off
title WorldCup2026 Cloudflare Growth Sync Loop
cd /d "D:\Social-main"

:loop
echo [%date% %time%] Syncing Cloudflare growth data...
python "admin\sync_cloudflare.py"
echo [%date% %time%] Next sync in 1 hour. Keep this window open.
timeout /t 3600 /nobreak
goto loop
