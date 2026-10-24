@echo off
title Intelligent Decoy Defense System - SOC Console
cd /d "%~dp0"
echo Launching Cyber SOC Dashboard on http://localhost:8501 ...
.\.venv\Scripts\streamlit.exe run application/dashboard.py
pause
