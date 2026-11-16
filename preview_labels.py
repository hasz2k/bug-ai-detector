"""Podgląd etykiet YOLO naniesionych na zrzuty (do ręcznej kontroli zbioru).

Użycie:
    python preview_labels.py dataset_real            # zbiór z collect_real.py
    python preview_labels.py dataset --split train   # dowolny zbiór YOLO

Wynik:
    <root>/preview/<nazwa>.png   każdy zrzut z ramkami
    <root>/preview_sheet.png     plansza ze wszystkimi podglądami (miniatury)
Ramki z <root>/suggested_bugs/ (podpowiedzi z reguł DOM) są rysowane cienko i opisane znakiem '?'.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

NAMES = ["button", "link", "input", "checkbox", "select", "ui_modal",
         "bug_clipping", "bug_text_overflow", "bug_overlap"]
COLORS = ["#00aa00", "#0066ff", "#aa00ff", "#ff9900", "#00cccc",
          "#ff00aa", "#ff0000", "#ee00ee", "#d4c800"]


def draw(im: Image.Image, label_file: Path, width: int, suffix: str = "") -> None:
    if not label_file.exists():
        return
    W, H = im.size
    d = ImageDraw.Draw(im)
    for line in label_file.read_text().splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        c = int(parts[0])
        x, y, w, h = (float(v) for v in parts[1:])
        x, y, w, h = x * W, y * H, w * W, h * H
        col = COLORS[c % len(COLORS)]
        d.rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], outline=col, width=width)
        d.text((x - w / 2 + 3, y - h / 2 + 2), NAMES[c] + suffix, fill=col)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--split", default="val")
    args = ap.parse_args()

    img_dir = args.root / "images" / args.split
    lbl_dir = args.root / "labels" / args.split
    sug_dir = args.root / "suggested_bugs"
    out_dir = args.root / "preview"
    out_dir.mkdir(exist_ok=True)

    thumbs = []
    for img_path in sorted(img_dir.glob("*.png")):
        im = Image.open(img_path).convert("RGB")
        draw(im, lbl_dir / f"{img_path.stem}.txt", 3)
        draw(im, sug_dir / f"{img_path.stem}.txt", 1, "?")
        im.save(out_dir / img_path.name)
        t = im.copy()
        t.thumbnail((640, 400))
        d = ImageDraw.Draw(t)
        d.rectangle([0, 0, t.width, 14], fill="#000000")
        d.text((3, 1), img_path.stem, fill="#ffffff")
        thumbs.append(t)

    if not thumbs:
        print("Brak obrazów w", img_dir)
        return
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 640, rows * 400), "#222222")
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % cols) * 640, (i // cols) * 400))
    sheet.save(args.root / "preview_sheet.png")
    print(f"Podglądów: {len(thumbs)} -> {out_dir}")
    print("Plansza:", args.root / "preview_sheet.png")


if __name__ == "__main__":
    main()
