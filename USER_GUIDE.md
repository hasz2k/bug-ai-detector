# 📖 User Guide / Podręcznik Użytkownika — Bug AI Detector Engine

[English](#english) | [Polski](#polski)

---

## 🇬🇧 English

Welcome to the **Bug AI Detector Engine User Guide**. This document provides complete instructions on running, configuring, operating, navigating, and managing the vision detection pipeline, testing workflows, and executive reporting.

### 📑 Table of Contents

1. [Getting Started & Installation](#1-getting-started--installation)
2. [Environment Variables & Backend Configuration](#2-environment-variables--backend-configuration)
3. [Single-Monitor Testing Workflow (Wayland / X11)](#3-single-monitor-testing-workflow-wayland--x11)
4. [Dashboard Overview & Key Metrics](#4-dashboard-overview--key-metrics)
5. [Autonomous QA Agent Execution](#5-autonomous-qa-agent-execution)
6. [Standalone HTML Model Verification](#6-standalone-html-model-verification)
7. [Issue Tracking & Integrations (Jira / Redmine)](#7-issue-tracking--integrations-jira--redmine)
8. [Executive Reporting (PDF / CSV)](#8-executive-reporting-pdf--csv)

---

### 1. Getting Started & Installation

#### 🌐 Live Demo Access
You can launch the dashboard directly in your browser via GitHub Pages without local setup:  
🔗 https://hasz2k.github.io/bug-ai-detector/

#### 💻 Running Locally by Operating System

First, clone the repository:
```bash
git clone https://github.com/hasz2k/bug-ai-detector.git
cd bug-ai-detector
```

##### Windows
* **Method 1 (File Explorer):** Open the project folder and double-click `index.html`.
* **Method 2 (PowerShell / Command Prompt):**
  ```powershell
  start index.html
  ```
* **Method 3 (Python Local HTTP Server):**
  ```cmd
  python -m http.server 8085
  ```
  Navigate to `http://localhost:8085`.

##### macOS
* **Method 1 (Finder):** Locate the cloned folder and double-click `index.html`.
* **Method 2 (Terminal):**
  ```bash
  open index.html
  ```
* **Method 3 (Python Local Server):**
  ```bash
  python3 -m http.server 8085
  ```
  Navigate to `http://localhost:8085`.

##### Linux (CachyOS / Arch / Ubuntu / Debian)
* **Method 1 (Terminal - Default Browser):**
  ```bash
  xdg-open index.html
  ```
* **Method 2 (Python Local Server):**
  ```bash
  python3 -m http.server 8085
  ```
  Navigate to `http://localhost:8085`.

---

### 2. Environment Variables & Backend Configuration

#### ⚙️ Backend Configuration (`backend/server.py`)
The inference server supports runtime tuning via environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `IMGSZ` | `1280` | Inference resolution (must match model export size, `1280` for v4) |
| `CONF` | `0.25` | Minimum confidence threshold (`0.35–0.45` recommended to filter UI noise) |
| `CAPTURE_REGION` | `None` | Screen crop `"left,top,width,height"` (e.g., `"0,0,960,1080"`) |
| `CAPTURE_MONITOR` | `1` | Monitor index for X11 `mss` capture |
| `FRAME_INTERVAL` | `0.005` | Delay between screen capture iterations (seconds) |

---

### 3. Single-Monitor Testing Workflow (Wayland / X11)

When testing on a single monitor, capturing the full screen while the dashboard is visible causes the model to analyze the dashboard itself. To isolate your target application:

1. **Tile windows side-by-side (50/50 split):**
   * **Left half (`0,0,960,1080`):** Open your target web page or local test file (e.g., `test.html`).
   * **Right half:** Open the Bug AI Detector Dashboard (`http://localhost:8085`).
2. **Start the backend with `CAPTURE_REGION`:**
   ```bash
   CONF=0.35 CAPTURE_REGION="0,0,960,1080" python backend/server.py
   ```
3. **Inspect live telemetry:** The **Live AI Vision Telemetry** panel will stream detections exclusively from the left browser window.

---

### 4. Dashboard Overview & Key Metrics

* **Header Bar:** Displays real-time WebSocket connection status (`Live Streaming` / `Live Demo`), active inference FPS counter, and the `PL / EN` language selector.
* **KPI Cards:** Tracks critical blockers, total detected visual anomalies, scenario coverage, and active AI agent bots.
* **Live AI Vision Telemetry Stream:** Displays real-time object detections (`button`, `link`, `input`, `checkbox`, `select`, `ui_modal`, `bug_clipping`, `bug_text_overflow`, `bug_overlap`), confidence scores, and relative coordinates (`T` / `L` / `W` / `H`).
* **Analytics Charts:** Interactive line and doughnut charts tracking bug detection trends across builds and defect classification breakdowns.

---

### 5. Autonomous QA Agent Execution

1. In the **Autonomous QA Agent Launcher** card, enter the target web application URL (e.g., `http://localhost:8085`).
2. Click **Run Agent Exploration**.
3. The Playwright engine will launch headless in the background, navigate the site, perform assertions, and stream telemetry data back to the dashboard.

---

### 6. Standalone HTML Model Verification

To test model accuracy on a local HTML file without screen capture overhead:
```bash
python test_model.py path/to/test.html --weights yolov8_ui_bugs_v4.pt
```
Annotated screenshots are saved automatically to `runs/detect/predict*/`.

---

### 7. Issue Tracking & Integrations (Jira / Redmine)

1. Under **Export Issue to Tracker**, enter:
   * **Bug Summary / Title**
   * **Reproduction details & logs**
2. Click **Jira Cloud** or **Redmine**.
3. A toast notification will confirm creation and show the ticket identifier.

---

### 8. Executive Reporting (PDF / CSV)

1. In the **Executive Reports** panel, click **Generate PDF & CSV Reports**.
2. Once processing completes, download links for the generated `.pdf` and `.csv` files will appear below the button.

---

## 🇵🇱 Polski

Witaj w **Podręczniku Użytkownika Bug AI Detector Engine**. Dokument zawiera kompletny instruktaż obsługi systemu, konfiguracji parametrów inferencji, przeprowadzenia testów oraz pracy z raportami.

### 📑 Spis treści

1. [Pierwsze Kroki i Uruchomienie](#1-pierwsze-kroki-i-uruchomienie)
2. [Zmienne Środowiskowe i Konfiguracja Backendu](#2-zmienne-środowiskowe-i-konfiguracja-backendu)
3. [Praca na Jednym Monitorze (Wayland / X11)](#3-praca-na-jednym-monitorze-wayland--x11)
4. [Nawigacja po Dashboardzie i Wskaźniki KPI](#4-nawigacja-po-dashboardzie-i-wskaźniki-kpi)
5. [Uruchamianie Agenta Autonomicznego](#5-uruchamianie-agenta-autonomicznego)
6. [Izolowany Test Modelu na Pliku HTML](#6-izolowany-test-modelu-na-pliku-html)
7. [Eksport Zgłoszeń (Jira / Redmine)](#7-eksport-zgłoszeń-jira--redmine)
8. [Generowanie Raportów (PDF / CSV)](#8-generowanie-raportów-pdf--csv)

---

### 1. Pierwsze Kroki i Uruchomienie

#### 🌐 Dostęp Online (Live Demo)
Aplikację można otworzyć w przeglądarce za pośrednictwem serwisu GitHub Pages:  
🔗 https://hasz2k.github.io/bug-ai-detector/

#### 💻 Uruchamianie Lokalne na Różnych Systemach

Pobierz repozytorium:
```bash
git clone https://github.com/hasz2k/bug-ai-detector.git
cd bug-ai-detector
```

##### Windows
* **Metoda 1 (Eksplorator plików):** Otwórz folder z projektem i kliknij dwukrotnie plik `index.html`.
* **Metoda 2 (PowerShell):**
  ```powershell
  start index.html
  ```
* **Metoda 3 (Lokalny serwer Python):**
  ```cmd
  python -m http.server 8085
  ```
  Otwórz w przeglądarce: `http://localhost:8085`.

##### macOS
* **Metoda 1 (Finder):** Wejdź do folderu i kliknij dwukrotnie `index.html`.
* **Metoda 2 (Terminal):**
  ```bash
  open index.html
  ```
* **Metoda 3 (Serwer Python):**
  ```bash
  python3 -m http.server 8085
  ```
  Otwórz: `http://localhost:8085`.

##### Linux (CachyOS / Arch / Ubuntu / Debian)
* **Metoda 1 (Terminal):**
  ```bash
  xdg-open index.html
  ```
* **Metoda 2 (Serwer Python):**
  ```bash
  python3 -m http.server 8085
  ```
  Otwórz: `http://localhost:8085`.

---

### 2. Zmienne Środowiskowe i Konfiguracja Backendu

#### ⚙️ Konfiguracja Backendu (`backend/server.py`)
Serwer inferencji obsługuje konfigurację w locie za pomocą zmiennych środowiskowych:

| Zmienna | Domyślnie | Opis |
| :--- | :--- | :--- |
| `IMGSZ` | `1280` | Rozdzielczość inferencji (zgodna z rozmiarem eksportu modelu, `1280` dla v4) |
| `CONF` | `0.25` | Minimalny próg pewności detekcji (`0.35–0.45` zalecane do odfiltrowania szumu) |
| `CAPTURE_REGION` | `None` | Wycinek ekranu `"left,top,width,height"` (np. `"0,0,960,1080"`) |
| `CAPTURE_MONITOR` | `1` | Numer monitora dla przechwytywania X11 (`mss`) |
| `FRAME_INTERVAL` | `0.005` | Pauza między kolejnymi zrzutami ekranu (w sekundach) |

---

### 3. Praca na Jednym Monitorze (Wayland / X11)

Podczas testów na jednym monitorze przechwytywanie pełnego ekranu powoduje analizę samego okna Dashboardu. Aby odizolować badaną stronę:

1. **Ustaw dwa okna obok siebie (podział 50/50):**
   * **Lewa połowa (`0,0,960,1080`):** Otwórz badaną stronę lub lokalny plik testowy (np. `test.html`).
   * **Prawa połowa:** Otwórz Dashboard Bug AI Detector (`http://localhost:8085`).
2. **Uruchom backend z parametrem `CAPTURE_REGION`:**
   ```bash
   CONF=0.35 CAPTURE_REGION="0,0,960,1080" python backend/server.py
   ```
3. **Obserwuj telemetrię na żywo:** Panel **Telemetria Vision AI na żywo** będzie pokazywał wyłącznie obiekty z lewego okna przeglądarki.

---

### 4. Nawigacja po Dashboardzie i Wskaźniki KPI

* **Pasek Nagłówka:** Wyświetla status połączenia WebSocket (`Transmisja na żywo` / `Live Demo`), aktualną liczbę klatek na sekundę (FPS) oraz przełącznik języka `PL / EN`.
* **Karty KPI:** Monitorują liczbę blokerów krytycznych, wykryte usterki wizualne, pokrycie scenariuszy oraz aktywne boty.
* **Telemetria Vision AI na Żywo:** Prezentuje wykryte klasy (`button`, `link`, `input`, `checkbox`, `select`, `ui_modal`, `bug_clipping`, `bug_text_overflow`, `bug_overlap`), pewność predykcji oraz współrzędne procentowe (`T` / `L` / `W` / `H`).
* **Wykresy Analityczne:** Śledzą dynamikę wykryć w kolejnych buildach oraz kategoryzację wykrytych błędów.

---

### 5. Uruchamianie Agenta Autonomicznego

1. W sekcji **Autonomous QA Agent Launcher** wpisz adres URL testowanej aplikacji (np. `http://localhost:8085`).
2. Kliknij **Run Agent Exploration**.
3. Silnik Playwright uruchomi się bezgłowo w tle, wykona inspekcję strony, przeprowadzi asercje i przesyła dane telemetryczne z powrotem do dashboardu.

---

### 6. Izolowany Test Modelu na Pliku HTML

Aby przetestować skuteczność modelu na pliku HTML bez udziału dashboardu i przechwytywania ekranu:
```bash
python test_model.py sciezka/do/test.html --weights yolov8_ui_bugs_v4.pt
```
Wynikowy zrzut z naniesionymi ramkami zapisze się automatycznie w katalogu `runs/detect/predict*/`.

---

### 7. Eksport Zgłoszeń (Jira / Redmine)

1. W module **Export Issue to Tracker** podaj:
   * **Tytuł / Podsumowanie usterki**
   * **Szczegóły odtworzenia i logi**
2. Kliknij przycisk **Jira Cloud** lub **Redmine**.
3. Powiadomienie toast wyświetli numer wygenerowanego zgłoszenia.

---

### 8. Generowanie Raportów (PDF / CSV)

1. W sekcji **Executive Reports** kliknij **Generate PDF & CSV Reports**.
2. Po zakończeniu generowania poniżej pojawią się bezpośrednie linki do pobrania plików `.pdf` i `.csv`.

---

## 👤 Author & Support / Autor i Wsparcie

* 👤 **Author:** `@hasz2k`
* ₿ **Bitcoin Address:** `bc1pjgctwfj5csuffdt54cl663830e77d88a65agatx2csfffedwr73q7hegq9`
