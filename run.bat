@echo off
REM ============================================================
REM  Launcher Stick PS2 -> Mouse
REM  Klik dua kali file ini untuk menjalankan program.
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment tidak ditemukan di .venv\
    echo [INFO]  Jalankan dulu: python -m venv .venv
    echo [INFO]  Lalu: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Menjalankan Stick PS2 -^> Mouse...
echo.
.venv\Scripts\python.exe -u -m src.main
echo.
echo Program selesai.
pause
endlocal
