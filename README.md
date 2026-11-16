# 🐞 Bug AI Detector Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF)](https://docs.ultralytics.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-v3.4-38B2AC)](https://tailwindcss.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Autonomous_Agent-45BA4B)](https://playwright.dev/)

[ English ](#-english) | [ Polski ](#-polski)

---

## 🇬🇧 English

### Overview
**Bug AI Detector Engine** is a Quality Assurance automation suite combining custom YOLOv8 computer vision (`IMGSZ=1280`), native Linux Wayland/X11 screen capture, synthetic & real-world dataset generation tools, and real-time WebSocket telemetry streams to detect UI components and visual layout defects.

### 🌟 Key Features
- **Live Vision AI Telemetry**: Non-blocking frame inference over WebSockets (`/ws/stream`) with live bounding-box rendering and FPS monitoring.
- **Native Wayland & X11 Capture**: Automatic session detection supporting KDE Plasma Wayland (`spectacle` via `/dev/shm` RAM buffer) and X11 (`mss`), plus `CAPTURE_REGION` cropping.
- **9-Class UI & Bug Detection Model (v4)**: Detects standard controls (`button`, `link`, `input`, `checkbox`, `select`, `ui_modal`) and visual defects (`bug_clipping`, `bug_text_overflow`, `bug_overlap`).
- **Dataset & Evaluation Toolkit**: Includes synthetic HTML bug generator (`gen_dataset.py`), `robots.txt`-compliant real web scraper (`collect_real.py`), class balancer (`merge_real.py`), label visualizer (`preview_labels.py`), and isolated HTML tester (`test_model.py`).
- **Multi-Engine Inference**: Automatic loader prioritizing OpenVINO / ONNX / PyTorch on CPU and TensorRT `.engine` / PyTorch on GPU.
- **Multilingual Dashboard (i18n)**: Instant PL/EN interface language toggle with `localStorage` state persistence and GitHub Pages Demo Mode fallback.

---

### 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────┐
│              Single Page Application (SPA)              │
│       (Tailwind CLI + Chart.js + i18n Engine)           │
└────────────────────────────▲────────────────────────────┘
                             │  WebSocket / HTTP API
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend Engine                  │
├────────────────────────────┬────────────────────────────┤
│ Vision AI Telemetry        │ Screen Capture Worker      │
│  └─ YOLOv8 (1280px, 9 cls) │  └─ Wayland (/dev/shm) /X11│
└────────────────────────────┴────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│       Dataset Toolkit (gen_dataset / collect_real)      │
└─────────────────────────────────────────────────────────┘

🚀 Quick Start
Prerequisites

    Python 3.10+

    Node.js & npm (optional, for rebuilding Tailwind CSS)

    Chromium / Playwright (playwright install chromium)

    spectacle (for KDE Plasma Wayland capture) or X11 session (mss)

Installation & Execution

    Clone the repository:
    Bash

    git clone [https://github.com/hasz2k/bug-ai-detector.git](https://github.com/hasz2k/bug-ai-detector.git)
    cd bug-ai-detector

    Setup Virtual Environment:
    Bash

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium

    Start Backend Server (with optional environment tuning):
    Bash

    IMGSZ=1280 CONF=0.35 python backend/server.py

    To capture a specific screen region (e.g., left half of a 1920×1080 display):
    Bash

    CONF=0.35 CAPTURE_REGION="0,0,960,1080" python backend/server.py

    Start Frontend Dashboard:
    Bash

    python -m http.server 8085

    Open http://localhost:8085 in your web browser.

🎯 Dataset Pipeline & Testing

    Generate synthetic UI & bug samples:
    Bash

    python gen_dataset.py --root ./dataset_synth --count 1500

    Collect real websites & balance classes:
    Bash

    python collect_real.py --urls urls_train.txt --root dataset_real_big --crawl 8 --scrolls 2 --test-frac 0.25
    python preview_labels.py dataset_real_big --split train
    python merge_real.py --real dataset_real_big --target ./dataset_synth

    Test model on a standalone HTML file:
    Bash

    python test_model.py test.html --weights yolov8_ui_bugs_v4.pt

    Export weights to ONNX / OpenVINO:
    Bash

    python export_ui_model.py --weights yolov8_ui_bugs_v4.pt --format onnx --imgsz 1280 --fp32
    

👤 Author & Support

    👤 Author: @hasz2k

    ₿ Bitcoin Address: bc1pjgctwfj5csuffdt54cl663830e77d88a65agatx2csfffedwr73q7hegq9

🇵🇱 Polski
Opis projektu

Bug AI Detector Engine to narzędzie automatyzacji Quality Assurance (QA) łączące dedykowany model wizji komputerowej YOLOv8 (IMGSZ=1280), natywne przechwytywanie ekranu pod Linuxem (Wayland / X11), potok generowania danych treningowych oraz strumieniowanie telemetrii WebSocket w czasie rzeczywistym do wykrywania elementów UI oraz wizualnych usterek układu.
🌟 Główne Funkcjonalności

    Telemetria Vision AI na Żywo: Nieblokująca inferencja klatek przez WebSocket (/ws/stream) z dynamicznym rysowaniem ramek detekcji (bounding boxes) i licznikiem FPS.

    Natywne Przechwytywanie Wayland i X11: Automatyczne wykrywanie sesji z obsługą KDE Plasma Wayland (spectacle z buforem RAM /dev/shm) oraz X11 (mss), wraz z wycinaniem obszaru CAPTURE_REGION.

    9-Klasowy Model UI i Defektów (v4): Wykrywa standardowe kontrolki (button, link, input, checkbox, select, ui_modal) oraz błędy wizualne (bug_clipping, bug_text_overflow, bug_overlap).

    Zestaw Narzędzi Danych i Walidacji: Generator syntetycznych stron z błędami (gen_dataset.py), scraper prawdziwych serwisów respektujący robots.txt (collect_real.py), skrypt balansowania klas (merge_real.py), podgląd etykiet (preview_labels.py) oraz izolowany tester plików HTML (test_model.py).

    Wielosilnikowy Loader Wag: Automatyczny wybór OpenVINO / ONNX / PyTorch na CPU oraz TensorRT .engine / PyTorch na GPU.

    Wielojęzyczny Dashboard (i18n): Przełącznik języka (PL / EN) z pamięcią stanu w localStorage oraz trybem Demo dla GitHub Pages.

🚀 Szybki Start
Wymagania wstępne

    Python 3.10+

    Chromium / Playwright (playwright install chromium)

    spectacle (dla sesji KDE Plasma Wayland) lub sesja X11 (mss)

Instalacja i Uruchomienie

    Sklonuj repozytorium:
    Bash

    git clone [https://github.com/hasz2k/bug-ai-detector.git](https://github.com/hasz2k/bug-ai-detector.git)
    cd bug-ai-detector

    Skonfiguruj środowisko wirtualne Python:
    Bash

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium

    Uruchom serwer Backendowy (FastAPI):
    Bash

    IMGSZ=1280 CONF=0.35 python backend/server.py

    Przechwytywanie wybranego wycinka ekranu (np. lewa połowa ekranu 1920×1080):
    Bash

    CONF=0.35 CAPTURE_REGION="0,0,960,1080" python backend/server.py

    Uruchom Dashboard UI:
    Bash

    python -m http.server 8085

    Otwórz w przeglądarce: http://localhost:8085.

👤 Author & Support / Autor i Wsparcie

    👤 Author: @hasz2k

    ₿ Bitcoin Address: bc1pjgctwfj5csuffdt54cl663830e77d88a65agatx2csfffedwr73q7hegq9
    
📄 License / Licencja

Distributed under the MIT License. See LICENSE for details. / Projekt udostępniany na licencji MIT.
