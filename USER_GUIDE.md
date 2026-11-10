# 📖 User Guide / Podręcznik Użytkownika — Bug AI Detector Engine

[ English ](#-english) | [ Polski ](#-polski)

---

## 🇬🇧 English

Welcome to the **Bug AI Detector Engine** User Guide. This document provides complete instructions on running, operating, navigating, and managing testing workflows.

---

### 📑 Table of Contents
1. [Getting Started & Installation](#1-getting-started--installation)
2. [Dashboard Overview & Key Metrics](#2-dashboard-overview--key-metrics)
3. [Autonomous QA Agent Execution](#3-autonomous-qa-agent-execution)
4. [Issue Tracking & Integrations (Jira / Redmine)](#4-issue-tracking--integrations-jira--redmine)
5. [Executive Reporting (PDF / CSV)](#5-executive-reporting-pdf--csv)

---

### 1. Getting Started & Installation

#### 🌐 Live Demo Access
You can launch the dashboard directly in your browser via GitHub Pages without local setup:  
🔗 [**https://hasz2k.github.io/bug-ai-detector/**](https://hasz2k.github.io/bug-ai-detector/)

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

### 2. Dashboard Overview & Key Metrics

* **Header Bar**: Displays real-time connection status (*Live Streaming* / *Live Demo*), active FPS counter, and the **PL / EN** language selector.
* **KPI Cards**: Tracks critical blockers, total detected visual anomalies, scenario coverage, and active AI agent bots.
* **Live AI Vision Telemetry Stream**: Shows a live stream with bounding boxes superimposed over detected UI elements (`ui_button`, `ui_input`, `ui_toast`).
* **Analytics Charts**: Interactive line and doughnut charts tracking bug detection trends vs build iterations and defect classifications.

---

### 3. Autonomous QA Agent Execution

1. In the **Autonomous QA Agent Launcher** card, enter the target web application URL (e.g., `http://localhost:8085`).
2. Click **Run Agent Exploration**.
3. The Playwright engine will launch headless in the background, navigate the site, perform assertions, and stream telemetry data back to the dashboard.

---

### 4. Issue Tracking & Integrations (Jira / Redmine)

1. Under **Export Issue to Tracker**, enter:
   - **Bug Summary / Title**
   - **Reproduction details & logs**
2. Click **Jira Cloud** or **Redmine**.
3. A toast notification will confirm creation and show the ticket identifier.

---

### 5. Executive Reporting (PDF / CSV)

1. In the **Executive Reports** panel, click **Generate PDF & CSV Reports**.
2. Once processing completes, download links for the generated `.pdf` and `.csv` files will appear below the button.

---

## 🇵🇱 Polski

Witaj w Podręczniku Użytkownika **Bug AI Detector Engine**. Dokument zawiera kompletny instruktaż obsługi systemu, przeprowadzenia testów oraz pracy z raportami.

---

### 📑 Spis treści
1. [Pierwsze Kroki i Uruchomienie](#1-pierwsze-kroki-i-uruchomienie)
2. [Nawigacja po Dashboardzie i Wskaźniki KPI](#2-nawigacja-po-dashboardzie-i-wskaźniki-kpi)
3. [Uruchamianie Agenta Autonomicznego](#3-uruchamianie-agenta-autonomicznego)
4. [Eksport Zgłoszeń (Jira / Redmine)](#4-eksport-zgłoszeń-jira--redmine)
5. [Generowanie Raportów (PDF / CSV)](#5-generowanie-raportów-pdf--csv)

---

### 1. Pierwsze Kroki i Uruchomienie

#### 🌐 Dostęp Online (Live Demo)
Aplikację można otworzyć w przeglądarce za pośrednictwem serwisu GitHub Pages:  
🔗 [**https://hasz2k.github.io/bug-ai-detector/**](https://hasz2k.github.io/bug-ai-detector/)

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

### 2. Nawigacja po Dashboardzie i Wskaźniki KPI

* **Pasek Nagłówka**: Wyświetla status połączenia na żywo (*Live Streaming* / *Live Demo*), płynność klatek (FPS) oraz przełącznik języka **PL / EN**.
* **Karty KPI**: Monitorują liczbę blokerów krytycznych, łączną liczbę anomalii, pokrycie scenariuszy oraz aktywne boty.
* **Stream Telemetrii Vision AI**: Prezentuje podgląd ekranu z nałożonymi w czasie rzeczywistym ramkami wykrytych obiektów UI (`ui_button`, `ui_input`, `ui_toast`).
* **Wykresy Analityczne**: Śledzą dynamikę wykryć w kolejnych buildach oraz kategoryzację typów błędów.

---

### 3. Uruchamianie Agenta Autonomicznego

1. W sekcji **Autonomous QA Agent Launcher** wpisz adres URL testowanej aplikacji (np. `http://localhost:8085`).
2. Kliknij **Run Agent Exploration**.
3. Silnik Playwright uruchomi się bezgłowo w tle, wykona inspekcję i przesłanie zebranych danych telemetrycznych.

---

### 4. Eksport Zgłoszeń (Jira / Redmine)

1. W module **Export Issue to Tracker** podaj:
   - **Tytuł / Podsumowanie usterki**
   - **Szczegóły odtworzenia i logi**
2. Kliknij przycisk **Jira Cloud** lub **Redmine**.
3. Powiadomienie toast wyświetli numer wygenerowanego zgłoszenia.

---

### 5. Generowanie Raportów (PDF / CSV)

1. W sekcji **Executive Reports** kliknij **Generate PDF & CSV Reports**.
2. Po zakończeniu generowania poniżej pojawią się bezpośrednie linki do pobrania plików `.pdf` i `.csv`.