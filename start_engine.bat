@echo off
chcp 65001 > nul
echo 🚀 Inicjalizacja Bug AI Detector Engine (Windows)...

if not exist ".venv" (
    echo 📦 Tworzenie wirtualnego środowiska Python (.venv)...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo 📥 Instalowanie zależności wewnątrz venv...
    pip install uvicorn ultralytics mss
) else (
    call .venv\Scripts\activate.bat
)

echo ⚡ Uruchamianie serwera FastAPI na ws://localhost:8000/ws/stream
uvicorn backend.server:app --reload --port 8000
pause
