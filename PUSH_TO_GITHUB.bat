@echo off
title Push Intelligent Decoy Defense System to GitHub
cd /d "%~dp0"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd;%LOCALAPPDATA%\Programs\Git Credential Manager;%PATH%"
echo ========================================================
echo   Pushing to GitHub: atharva-kalaskar/Intelligent-Decoy-File-System
echo ========================================================
echo.
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Project successfully uploaded to GitHub!
) else (
    echo [INFO] If prompted for credentials, please sign in via browser or token.
)
echo.
pause
