# 🗺️ Product Roadmap / Mapa Drogowa — Bug AI Detector Engine

[ English ](#-english) | [ Polski ](#-polski)

---

## 🇬🇧 English

### Project Roadmap & Milestones

#### ✅ Phase 1-3: Core Engine, Telemetry & Integration (Completed)
- [x] High-frequency WebSocket telemetry streaming server in FastAPI.
- [x] Unified Single Page Application (SPA) dashboard (Tailwind CLI + Chart.js).
- [x] Real-time multilingual i18n support (PL/EN) with state persistence.
- [x] Full static fallback Demo Mode for GitHub Pages.
- [x] Autonomous Playwright browser crawling agent.
- [x] REST API exports to Jira Cloud and Redmine bug trackers.
- [x] Executive PDF (ReportLab) & CSV report generators.

#### 🟡 Phase 4: Dedicated Computer Vision Model (In Progress / Deployed)
- [x] Train script `train_ui_model.py` with multi-backend detection (CUDA / ROCm / MPS / CPU).
- [x] Dynamic model resolution in FastAPI: automatic loading of `yolov8_ui_bugs.pt` with fallback to `yolov8n.pt`.
- [x] Synthetic & Custom dataset pipeline setup (`dataset_ui.yaml`).
- [ ] Model conversion to **ONNX / TensorRT** execution engines for >100 FPS inference.
- [ ] Dataset expansion for complex visual glitches (*text overlapping*, *clipping*, *unrendered textures*).

#### 🔵 Phase 5: Standalone Desktop Packaging (Planned)
- [ ] Standalone executable bundle via **PyInstaller + pywebview**.
- [ ] Background process orchestrator (silent FastAPI server startup upon launcher execution).
- [ ] Multi-platform installers: Windows (`.exe`), Linux (`.AppImage`), macOS (`.dmg`).

#### 🟣 Phase 6: CI/CD Pipeline & Multi-Agent Exploration (Future Releases)
- [ ] CI/CD integration plugins (GitHub Actions / GitLab CI) as visual build gates.
- [ ] Parallel multi-agent Playwright exploration clusters.
- [ ] Embedded OCR engine (PaddleOCR / Tesseract) for UI spell-checking and localization validation.

---

## 🇵🇱 Polski

### Plan Rozwoju i Kamienie Milowe

#### ✅ Faza 1-3: Silnik Główny, Telemetria i Integracje (Zrealizowane)
- [x] Wysokowydajny serwer telemetrii WebSocket oparty na FastAPI.
- [x] Spójny dashboard SPA zbudowany z użyciem Tailwind CLI oraz Chart.js.
- [x] Wielojęzyczność (PL/EN i18n) działająca w czasie rzeczywistym.
- [x] Tryb Demo (fallback) przygotowany pod serwowanie na GitHub Pages.
- [x] Autonomiczny agent eksploracyjny bazujący na środowisku Playwright.
- [x] Integracja REST API z systemami śledzenia błędów Jira Cloud i Redmine.
- [x] Automatyczne generowanie raportów w formatach PDF oraz CSV.

#### 🟡 Faza 4: Dedykowany Model Computer Vision (Zrealizowana wdrożeniowo)
- [x] Dedykowany skrypt treningowy `train_ui_model.py` z auto-detekcją sprzętu (CUDA / ROCm / MPS / CPU).
- [x] Automatyczny wykrywacz autorskiego pliku wag `yolov8_ui_bugs.pt` z bezpiecznym fallbackiem do `yolov8n.pt`.
- [x] Konfiguracja rurociągu syntetycznego zbioru danych (`dataset_ui.yaml`).
- [ ] Eksport i konwersja wyuczonego modelu do formatów **ONNX / TensorRT** dla uzyskania wydajności >100 FPS.
- [ ] Rozbudowa zbioru danych o bardziej skomplikowane usterki (*mesh clipping*, *text overflow*, *unrendered textures*).

#### 🔵 Faza 5: Samodzielna Aplikacja Desktopowa (Planowane)
- [ ] Utworzenie pełnego pakietu dystrybucyjnego przy użyciu **PyInstaller + pywebview**.
- [ ] Menedżer procesów uruchamiający serwer FastAPI cicho w tle przy starcie okna GUI.
- [ ] Pakiety instalacyjne dla systemów Windows (`.exe`), Linux (`.AppImage`) oraz macOS (`.dmg`).

#### 🟣 Faza 6: CI/CD & Eksploracja Multi-Agentowa (Przyszłe Wydania)
- [ ] Integracja z systemami CI/CD (GitHub Actions / GitLab CI) w roli automatycznej bramki wizualnej.
- [ ] Architektura równoległej pracy wielu agentów Playwright.
- [ ] Moduł OCR (PaddleOCR / Tesseract) do weryfikacji błędów językowych i literówek w interfejsie.