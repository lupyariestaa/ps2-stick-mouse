@echo off
REM ============================================================
REM  Wizard Pemetaan Tombol - pandu tekan tombol satu per satu
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment tidak ditemukan di .venv\
    pause
    exit /b 1
)

echo Menjalankan wizard pemetaan tombol...
echo.
.venv\Scripts\python.exe -u -m src.diagnose wizard
echo.
pause
endlocal
