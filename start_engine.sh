#!/usr/bin/env bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Inicjalizacja Bug AI Detector Engine (Bash/Zsh)...${NC}"

if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Tworzenie wirtualnego środowiska Python (.venv)...${NC}"
    python3 -m venv .venv --system-site-packages
    source .venv/bin/activate
    echo -e "${BLUE}📥 Instalowanie zależności wewnątrz venv...${NC}"
    pip install fastapi uvicorn ultralytics mss websockets playwright
else
    source .venv/bin/activate
    if ! command -v uvicorn &> /dev/null; then
        pip install fastapi uvicorn ultralytics mss websockets playwright
    fi
fi

echo -e "${GREEN}⚡ Uruchamianie serwera FastAPI na ws://localhost:8000/ws/stream${NC}"
uvicorn backend.server:app --reload --port 8000
