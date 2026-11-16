# 🗺️ Product Roadmap / Mapa Drogowa — Bug AI Detector Engine

[ English ](#-english) | [ Polski ](#-polski)

---

## 🇬🇧 English

### Project Roadmap & Milestones

#### ✅ Phase 1-3: Core Engine, Telemetry & Integration (Completed)
- [x] High-frequency WebSocket telemetry streaming server in FastAPI (`/ws/stream`).
- [x] Unified Single Page Application (SPA) dashboard (Tailwind CLI + Chart.js).
- [x] Real-time multilingual i18n support (PL/EN) with `localStorage` state persistence.
- [x] Full static fallback Demo Mode for GitHub Pages.
- [x] Native screen capture worker supporting **Wayland** (KDE `spectacle` via `/dev/shm` RAM buffer) and **X11** (`mss`), with configurable `CAPTURE_REGION`.
- [x] Non-blocking thread-pool inference (`asyncio.to_thread`) with percentage-based bounding boxes and live FPS counter.

#### 🟡 Phase 4: Dedicated Computer Vision Model (v4 Deployed / v5 Scaling in Progress)
- [x] Unified 9-class UI & visual defect schema (`dataset_ui.yaml`: `button`, `link`, `input`, `checkbox`, `select`, `ui_modal`, `bug_clipping`, `bug_text_overflow`, `bug_overlap`).
- [x] Synthetic HTML/CSS layout & bug generator (`gen_dataset.py`) with automated DOM ground-truth labeling.
- [x] Ethical real-world web scraper (`collect_real.py` respecting `robots.txt`) and class-balancing merger (`merge_real.py`).
- [x] Label verification (`preview_labels.py`), isolated HTML testing (`test_model.py`), and ONNX / OpenVINO export pipeline (`export_ui_model.py`).
- [x] Multi-backend model resolver in FastAPI (`OpenVINO` / `ONNX` / `TensorRT` / `PyTorch`) defaulting to native `IMGSZ=1280` for v4 weights (`mAP50 = 0.90` mixed validation, `0.65–0.69` on unseen real websites).
- [ ] **Dataset Scaling & High-Density Object Training (v5):** Train next-generation weights on a significantly larger volume of high-density screenshots (dozens/hundreds of UI objects per frame) to improve recall on dense navigation bars, icon buttons, and small links.
- [ ] **Automated CSS Bug Injection on Real Pages:** Extend `collect_real.py` to inject controlled CSS mutations (`overflow: hidden` text clipping, negative-margin overlaps, forced container overflows) directly into real-world DOMs with exact bounding-box extraction.
- [ ] **Bug-Only Inspection Mode & Single-Monitor Overlay:** Add class filtering (`FILTER_BUGS_ONLY=1` for classes 6–8) and self-window masking / transparent OS overlay to prevent dashboard self-detection on single-monitor setups.
- [ ] **Real Backend Action Handlers:** Replace mock endpoints in `/api/run-agent` (live Playwright audit), `/api/create-issue` (Jira Cloud / Redmine REST API), and `/api/export-report` (PDF/CSV generation).

#### 🔵 Phase 5: Standalone Desktop Packaging & Inference Acceleration (Planned)
- [ ] Direct **PipeWire / XDG Desktop Portal** Wayland frame capture to eliminate external subprocess overhead.
- [ ] Production quantization to **OpenVINO INT8/FP16** (CPU) and **TensorRT** (GPU) for >100 FPS inference at `1280px`.
- [ ] Standalone executable bundle via **PyInstaller + pywebview** with multi-platform installers (`.AppImage`, `.exe`, `.dmg`).

#### 🟣 Phase 6: CI/CD Pipeline & Multi-Agent Exploration (Future Releases)
- [ ] CI/CD integration plugins (GitHub Actions / GitLab CI) as automated visual regression gates.
- [ ] Parallel multi-agent Playwright exploration clusters.
- [ ] Embedded OCR engine (PaddleOCR / Tesseract) for UI spell-checking and localization validation.

---

## 🇵🇱 Polski

### Plan Rozwoju i Kamienie Milowe

#### ✅ Faza 1-3: Silnik Główny, Telemetria i Przechwytywanie Ekranu (Zrealizowane)
- [x] Wysokowydajny serwer telemetrii WebSocket oparty na FastAPI (`/ws/stream`).
- [x] Spójny dashboard SPA zbudowany z użyciem Tailwind CLI oraz Chart.js.
- [x] Wielojęzyczność (PL/EN i18n) działająca w czasie rzeczywistym z pamięcią stanu w `localStorage`.
- [x] Tryb Demo (fallback) przygotowany pod serwowanie na GitHub Pages.
- [x] Natywne przechwytywanie ekranu dla sesji **Wayland** (KDE `spectacle` z zapisem do pamięci operacyjnej `/dev/shm` bez zużycia dysku) oraz **X11** (`mss`), z obsługą wycinków `CAPTURE_REGION`.
- [x] Nieblokująca inferencja w osobnej puli wątków (`asyncio.to_thread`) z transmisją procentowych współrzędnych ramek oraz licznikiem FPS.

#### 🟡 Faza 4: Dedykowany Model Computer Vision (Wersja v4 wdrożona / Skalowanie v5)
- [x] Zunifikowany schemat 9 klas elementów UI i defektów (`dataset_ui.yaml`: `button`, `link`, `input`, `checkbox`, `select`, `ui_modal`, `bug_clipping`, `bug_text_overflow`, `bug_overlap`).
- [x] Generator syntetycznych stron HTML/CSS z celowymi usterkami (`gen_dataset.py`) i automatycznym wyliczaniem etykiet z DOM.
- [x] Scraper prawdziwych stron internetowych (`collect_real.py` respektujący `robots.txt`) oraz skrypt równoważenia rzadkich klas (`merge_real.py`).
- [x] Narzędzia kontroli etykiet (`preview_labels.py`), izolowanych testów HTML (`test_model.py`) oraz eksportu do ONNX / OpenVINO (`export_ui_model.py`).
- [x] Wielosilnikowy loader modeli w FastAPI (`OpenVINO` / `ONNX` / `TensorRT` / `PyTorch`) z domyślną rozdzielczością `IMGSZ=1280` dla wag v4 (`mAP50 = 0.90` na walidacji mieszanej, `0.65–0.69` na obcych stronach rzeczywistych).
- [ ] **Trenowanie modelu na znacznie większej liczbie obiektów (v5):** Przetrenowanie kolejnej wersji wag na znacznie większym wolumenie gęstych zrzutów ekranu (dziesiątki/setki obiektów na jednej klatce), aby podnieść czułość (recall) dla gęstych menu, przycisków ikonowych i małych linków.
- [ ] **Automatyczne wstrzykiwanie bugów CSS w prawdziwe strony:** Rozbudowa `collect_real.py` o wstrzykiwanie kontrolowanych mutacji CSS (ucinanie tekstu `overflow: hidden`, nachodzenie elementów, przepełnienia kontenerów) bezpośrednio w DOM prawdziwych serwisów z automatycznym zapisem ramek `bbox`.
- [ ] **Tryb „Tylko Błędy” i obsługa jednego monitora:** Dodanie filtrowania klas (`FILTER_BUGS_ONLY=1` dla klas 6–8) oraz maskowania okna samego dashboardu / przezroczystej nakładki systemowej, aby wyeliminować detekcję własnego UI na jednym monitorze.
- [ ] **Podpięcie właściwych akcji API:** Zastąpienie symulacji w `/api/run-agent` (audyt Playwright), `/api/create-issue` (integracja z Jira Cloud / Redmine) oraz `/api/export-report` (generowanie raportów PDF/CSV).

#### 🔵 Faza 5: Aplikacja Desktopowa i Optymalizacja FPS (Planowane)
- [ ] Bezpośredni strumień przechwytywania Wayland przez **PipeWire / XDG Desktop Portal** (eliminacja narzutu procesu zewnętrznego).
- [ ] Kwantyzacja i eksport produkcyjny do **OpenVINO INT8/FP16** (CPU) oraz **TensorRT** (GPU) w celu osiągnięcia >100 FPS przy `1280px`.
- [ ] Samodzielny pakiet dystrybucyjny (**PyInstaller + pywebview**) na Linux (`.AppImage`), Windows (`.exe`) i macOS (`.dmg`).

#### 🟣 Faza 6: CI/CD & Eksploracja Multi-Agentowa (Przyszłe Wydania)
- [ ] Integracja z systemami CI/CD (GitHub Actions / GitLab CI) w roli automatycznej bramki wizualnej.
- [ ] Architektura równoległej pracy wielu agentów Playwright.
- [ ] Moduł OCR (PaddleOCR / Tesseract) do weryfikacji błędów językowych i literówek w interfejsie.