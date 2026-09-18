@echo off
REM Restart Aparteman dev server cleanly: kills anything on port 8000, then starts fresh.
cd /d C:\Aparteman
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "127.0.0.1:8000" ^| findstr LISTENING') do (
    echo Killing old server PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo Starting server on http://127.0.0.1:8000 ...
C:\Users\MohammadJavad\.local\bin\uv.exe run python manage.py runserver
