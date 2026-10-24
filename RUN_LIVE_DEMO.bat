@echo off
title Intelligent Decoy Defense System - Live Demonstration
cd /d "%~dp0"
echo Launching Live Demonstration Console...
.\.venv\Scripts\python.exe demo_live.py
pause
