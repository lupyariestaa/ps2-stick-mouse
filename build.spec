# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller untuk Stick PS2 -> Mouse.

Build:
    .venv\\Scripts\\pyinstaller build.spec --noconfirm
Hasil: dist/StickMouse/StickMouse.exe
"""

block_cipher = None

a = Analysis(
    ["StickMouse.py"],
    pathex=[],
    binaries=[],
    # config.json TIDAK di-bundle; program akan otomatis membuatnya di
    # samping .exe agar mudah diedit pengguna.
    datas=[],
    hiddenimports=[
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "speech_recognition",
        "pyaudio",
        "pycaw",
        "comtypes",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StickMouse",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="StickMouse",
)
