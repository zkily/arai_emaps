@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Smart-EMAP (backend + Vite dev + dist + optional file watcher)...
py start.py
if errorlevel 1 pause
