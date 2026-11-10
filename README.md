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
**Bug AI Detector Engine** is a professional-grade Quality Assurance automation suite. It leverages custom computer vision (YOLOv8), autonomous web crawling agents (Playwright), and real-time WebSocket telemetry streams to detect visual bugs, layout overflows, mesh clipping, and UI anomalies across web and desktop applications.

### 🌟 Key Features
- **Live Vision AI Telemetry**: Real-time frame processing over WebSockets with live bounding box rendering.
- **Custom UI QA Model Pipeline**: Train specialized models on custom UI elements (`ui_button`, `ui_input`, `ui_modal`, `ui_toast`) and visual defects (`bug_clipping`, `bug_text_overflow`).
- **Autonomous QA Agent**: Driven by Playwright to automatically crawl target URLs, trigger interactions, and capture telemetry logs.
- **Issue Tracker Export**: Direct integration with **Jira Cloud** (ADF format) and **Redmine** REST APIs.
- **Executive Reporting**: Automated report generator producing standard **PDF** and **CSV** deliverables.
- **Multilingual Dashboard (i18n)**: Instant PL/EN interface language toggle with `localStorage` state persistence.
- **Production CSS Pipeline**: Minified and optimized stylesheet built via Tailwind CLI (`dist/output.css`).
- **Demo Mode Fallback**: Automatic mock telemetry simulation for static hosting environments (e.g., GitHub Pages).

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
│ Vision AI Telemetry        │ Playwright Autonomous Agent│
│  └─ YOLOv8 / YOLOv11 Model │  └─ Target UI Crawler      │
└────────────────────────────┴────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│            Jira / Redmine & PDF/CSV Exporter            │
└────────────────────────────┴────────────────────────────┘
```

---

### 🚀 Quick Start

#### Prerequisites
- Python 3.10+
- Node.js & npm (for Tailwind CLI building)
- Google Chrome / Chromium (for Playwright agent)

#### Installation & Execution

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hasz2k/bug-ai-detector.git
   cd bug-ai-detector
   ```

2. **Setup Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Build Production CSS:**
   ```bash
   npm install
   npm run build:css
   ```

4. **Start Backend Server:**
   ```bash
   python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Start Frontend Server:**
   ```bash
   python -m http.server 8085
   ```
   Open `http://localhost:8085` in your web browser.

---

### 🎯 Training Custom UI Model (Phase 4)

To train a dedicated UI detection model on your dataset:

```bash
python train_ui_model.py --dataset dataset_ui.yaml --epochs 50 --batch 16 --device auto
```

Copy the generated model weights to the project root:
```bash
cp runs/ui/bug_ai_ui_model_*/weights/best.pt ./yolov8_ui_bugs.pt
```
The FastAPI backend will automatically detect `yolov8_ui_bugs.pt` upon startup (falling back to `yolov8n.pt` if unavailable).

---

## 🇵🇱 Polski

### Opis projektu
**Bug AI Detector Engine** to zaawansowany system automatyzacji procesów Quality Assurance (QA). Wykorzystuje dedykowaną detekcję komputerową (YOLOv8), autonomiczne boty eksploracyjne (Playwright) oraz telemetrię WebSocket w czasie rzeczywistym do natychmiastowego identyfikowania usterek wizualnych, błędów układu (layout overflow, mesh clipping) oraz anomalii w aplikacjach webowych i desktopowych.

---

### 🌟 Główne Funkcjonalności
- **Telemetria Vision AI na Żywo**: Płynna analiza klatek w czasie rzeczywistym przez WebSocket z dynamicznym rysowaniem ramek detekcji (*bounding boxes*).
- **Dedykowany Pipeline Modelu UI QA**: Trenuj własne modele na komponentach interfejsu (`ui_button`, `ui_input`, `ui_modal`, `ui_toast`) oraz usterkach wizualnych (`bug_clipping`, `bug_text_overflow`).
- **Autonomiczny Agent QA**: Integracja z Playwright umożliwiająca samodzielną eksplorację adresów URL, symulację akcji użytkownika oraz rejestrację logów.
- **Bezpośrednia Integracja z Trackerami**: Jednoklikowy eksport zgłoszeń błędów do systemów **Jira Cloud** (format ADF) oraz **Redmine**.
- **Raporty Wykonawcze**: Automatyczny generator zbiorczych raportów w formatach **PDF** oraz **CSV**.
- **Wielojęzyczny Dashboard (i18n)**: Przełącznik języka (Polski / Angielski) działający w czasie rzeczywistym z pamięcią stanu w `localStorage`.
- **Produkcyjny Pipeline CSS**: Skompresowany i zoptymalizowany arkusz stylów via Tailwind CLI (`dist/output.css`).
- **Tryb Demo / Offline Fallback**: Automatyczna symulacja danych dla środowisk bez dostępnego serwera backendowego (np. GitHub Pages).

---

### 🚀 Szybki Start

#### Wymagania wstępne
- Python 3.10+
- Node.js & npm (do kompilacji CSS przez Tailwind CLI)
- Google Chrome / Chromium (dla agenta Playwright)

#### Instrukcja Krok po Kroku

1. **Sklonuj repozytorium:**
   ```bash
   git clone https://github.com/hasz2k/bug-ai-detector.git
   cd bug-ai-detector
   ```

2. **Skonfiguruj środowisko Python:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Zbuduj zoptymalizowany plik CSS:**
   ```bash
   npm install
   npm run build:css
   ```

4. **Uruchom serwer Backendowy (FastAPI):**
   ```bash
   python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Uruchom Dashboard UI:**
   ```bash
   python -m http.server 8085
   ```
   Otwórz przeglądarkę pod adresem: `http://localhost:8085`.

---

### 🎯 Trening Własnego Modelu UI (Faza 4)

Aby wyszkolić model na własnym zestawie danych UI:

```bash
python train_ui_model.py --dataset dataset_ui.yaml --epochs 50 --batch 16 --device auto
```

Po zakończeniu uczenia skopiuj wygenerowany plik wag do korzenia projektu:
```bash
cp runs/ui/bug_ai_ui_model_*/weights/best.pt ./yolov8_ui_bugs.pt
```
Serwer backendowy automatycznie wykryje plik `yolov8_ui_bugs.pt` przy następnym uruchomieniu (z bezpiecznym fallbackiem do `yolov8n.pt` w przypadku braku pliku).

---

## 📄 License / Licencja
Distributed under the MIT License. See `LICENSE` for details. / *Projekt udostępniany na licencji MIT.*