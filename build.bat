@echo off
REM ============================================================
REM  Build Stick PS2 -> Mouse menjadi .exe (folder dist/)
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment tidak ditemukan di .venv\
    pause
    exit /b 1
)

echo Membersihkan build lama...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo Membangun .exe dengan PyInstaller...
.venv\Scripts\pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] Build gagal.
    pause
    exit /b 1
)

echo.
echo Selesai! Hasil ada di: dist\StickMouse\StickMouse.exe
echo.
pause
endlocal
