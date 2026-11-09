# 🗺️ Bug AI Detector Engine — Development Roadmap

Ten dokument przedstawia aktualny stan prac oraz plany rozwoju projektu **Bug AI Detector**.

---

## 📌 Status Realizacji (Current Progress)

### ✅ Faza 1: Silnik Detekcji & Podstawowy Stream
- [x] Konfiguracja serwera FastAPI z cyklem życia `lifespan`.
- [x] Przechwytywanie ekranu `mss` w osobnym wątku `ThreadPoolExecutor`.
- [x] Detekcja obiektów UI przy użyciu modelu YOLOv8.
- [x] Dedykowana obsługa połączeń WebSocket (`ConnectionManager`).

### ✅ Faza 2: Autonomiczny Agent QA & Artefakty Sesji
- [x] Integracja silnika Playwright w trybie headless do eksploracji interfejsu.
- [x] Automatyczne nagrywanie sesji testowych do plików `.webm`.
- [x] Zapis szczegółowych logów wykonywanych kroków w plikach `.log`.
- [x] Statyczne serwowanie plików artefaktów (`/logs`, `/videos`).

### ✅ Faza 3: Integracje, Raportowanie & Bezpieczeństwo
- [x] Natywne REST API dla Jira Cloud (w formatowaniu ADF) oraz Redmine.
- [x] Powiadomienia webhook dla Slacka i Discorda (`allowed_mentions` policy).
- [x] Bezpieczny generator raportów PDF (ReportLab) oraz CSV (zabezpieczenie przed CSV Injection).
- [x] Rozwiązanie problemów CORS oraz elastyczna obsługa WebSocketów dla `localhost` i `127.0.0.1`.

---

## 🔮 Plany Rozwoju (Future Enhancements)

### 🚀 Faza 4: Dedykowany Model Computer Vision (Q1/Q2 2027)
- [ ] Trenowanie własnego modelu YOLO na dedykowanym zbiorze elementów UI (przyciski, inputy, modale, toasty błędów).
- [ ] Detekcja nakładających się lub przysłoniętych elementów (UX accessibility check).
- [ ] Automatyczne rozpoznawanie nieobsłużonych wyjątków w interfejsie graficznym.

### 🌐 Faza 5: Wielowątkowość i Skalowalność
- [ ] Obsługa wielu równoległych sesji testowych w kontenerach Docker.
- [ ] Panel zarządzania historią sesji testowych bezpośrednio z poziomu interfejsu HTML.
- [ ] Dedykowana integracja z GitHub Actions CI/CD.
