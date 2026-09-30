"""Entry point untuk packaging PyInstaller.

Dipisah dari src/main.py agar relative import di dalam package `src` tetap
bekerja saat dijalankan sebagai .exe.
"""

from src.main import main

if __name__ == "__main__":
    main()
