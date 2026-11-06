#!/usr/bin/fish

set GREEN '\033[0;32m'
set BLUE '\033[0;34m'
set NC '\033[0m'

echo -e "$BLUE🚀 Inicjalizacja Bug AI Detector Engine (Fish / CachyOS)...$NC"

if not test -d .venv
    echo -e "$BLUE📦 Tworzenie wirtualnego środowiska Python (.venv)...$NC"
    python3 -m venv .venv --system-site-packages
    source .venv/bin/activate.fish
    echo -e "$BLUE📥 Instalowanie zależności wewnątrz venv...$NC"
    pip install uvicorn ultralytics mss
else
    source .venv/bin/activate.fish
    # Szybkie upewnienie się, że uvicorn jest zainstalowany w venv
    if not command -v uvicorn > /dev/null
        pip install uvicorn ultralytics mss
    end
end

echo -e "$GREEN⚡ Uruchamianie serwera FastAPI na ws://localhost:8000/ws/stream$NC"
uvicorn backend.server:app --reload --port 8000
