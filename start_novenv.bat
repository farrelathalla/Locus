@echo off
setlocal

echo DNA Pathogenicity Analyzer
echo ===========================
echo.

if not exist ".env" (
    echo [WARN] File .env tidak ditemukan. Menyalin dari .env.example...
    copy .env.example .env
    echo [INFO] Edit file .env dan isi API key Anda, lalu jalankan ulang script ini.
    pause
    exit /b 1
)

echo [1/2] Menjalankan API server (FastAPI)...
start "API Server" cmd /k "cd /d %~dp0 && set PYTHONPATH=%~dp0 && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo [2/2] Menjalankan web server (Next.js)...
start "Web Server" cmd /k "cd /d %~dp0web && npm run dev"

echo.
echo Layanan berjalan:
echo   API  : http://localhost:8000
echo   Docs : http://localhost:8000/docs
echo   Web  : http://localhost:3000
echo.
echo Tekan tombol apa saja untuk menutup jendela ini...
pause > nul
