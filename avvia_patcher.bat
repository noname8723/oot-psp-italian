@echo off
title OOT PSP Italiano
cd /d "%~dp0"
where py >nul 2>nul && (py oot_psp_it_patch.py & goto fine)
where python >nul 2>nul && (python oot_psp_it_patch.py & goto fine)
echo Python non trovato. Installalo da https://www.python.org/downloads/ e spunta "Add python.exe to PATH".
:fine
echo.
pause
