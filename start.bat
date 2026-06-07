@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Smart-EMAP (backend + dist HTTP:3005 / HTTPS:5005)...
py start.py
if errorlevel 1 pause
