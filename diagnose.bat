@echo off
REM ============================================================
REM  Diagnostik Stik - lihat nilai axis & index tombol
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment tidak ditemukan di .venv\
    pause
    exit /b 1
)

echo Menjalankan diagnostik stik...
echo.
.venv\Scripts\python.exe -u -m src.diagnose %*
echo.
pause
endlocal
