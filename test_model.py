"""Test modelu na stronie HTML: zrzut ekranu strony + detekcja.

Użycie (z katalogu z yolov8_ui_bugs.pt):
    python test_model.py /sciezka/do/test.html
    python test_model.py /sciezka/do/test.html --conf 0.15 --width 1280

Wynik: test_html.png (zrzut) oraz obraz z ramkami w runs/detect/predict*/.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright
from ultralytics import YOLO


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path, help="ścieżka do pliku HTML")
    ap.add_argument("--weights", default="yolov8_ui_bugs.pt")
    ap.add_argument("--imgsz", type=int, default=1280)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=1000)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    url = args.html.expanduser().resolve().as_uri()
    shot = Path("test_html.png")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.goto(url)
        page.screenshot(path=str(shot), full_page=True)
        browser.close()
    print("Zrzut zapisany:", shot.resolve())

    model = YOLO(args.weights)
    results = model.predict(str(shot), imgsz=args.imgsz, conf=args.conf,
                            device=args.device, save=True)
    r = results[0]
    print("\nWykryte obiekty:")
    for box in r.boxes:
        print(f"  {model.names[int(box.cls[0])]:<18} {float(box.conf[0]):.2f}")
    print("\nObraz z ramkami:", Path(r.save_dir).resolve())


if __name__ == "__main__":
    main()
