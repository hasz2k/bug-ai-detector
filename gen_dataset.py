"""Generator syntetycznych zrzutów ekranu z bugami UI + etykiety YOLO.

Wzorowany na test.html (przepełnienie tekstu, ucięcie, nakładanie), ale z losowymi
kolorami, fontami, rozmiarami i układem, żeby model uczył się BUGÓW, a nie jednej strony.
Etykiety biorą się z DOM (getBoundingClientRect), więc ramki są dokładne.

Instalacja (raz):
    pip install playwright
    playwright install chromium

Użycie:
    python gen_dataset.py --root dataset --count 800
    # potem:
    python train_ui_model.py --dataset dataset/dataset_ui.yaml --base-model yolov8n.pt --imgsz 1280 --batch 8

Klasy (zgodne z ujednoliconym dataset_ui.yaml, pierwsze 5 = Twoja paczka):
    0 button, 1 link, 2 input, 3 checkbox, 4 select, 5 ui_modal,
    6 bug_clipping, 7 bug_text_overflow, 8 bug_overlap

UWAGA: numeracja bugów zmieniła się względem starszej wersji (było 5/6/7, jest 6/7/8).
Etykiety wygenerowane starą wersją trzeba przemapować albo wygenerować od nowa.
"""

from __future__ import annotations

import argparse
import random
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

NAMES = ["button", "link", "input", "checkbox", "select", "ui_modal",
         "bug_clipping", "bug_text_overflow", "bug_overlap"]

VIEWPORTS = [(1920, 1080), (1366, 768), (1280, 720), (1600, 900), (1536, 864)]
FONTS = ["Arial, sans-serif", "Georgia, serif", "'Courier New', monospace",
         "Verdana, sans-serif", "Tahoma, sans-serif", "system-ui, sans-serif"]
WORDS = ["KUP", "Zapisz", "Dalej", "Anuluj", "Zamów teraz", "Szczegóły", "Zaloguj",
         "Submit", "Pay now", "Wyślij", "Dodaj do koszyka", "Usuń", "Settings", "OK"]
LONG = ["Ten tekst jest za długi i zostanie ucięty",
        "Very long label that does not fit in the container",
        "Regulamin, polityka prywatności oraz warunki korzystania z usługi",
        "Przepełniony napis wychodzący poza ramkę elementu",
        "Subscription renewal terms and conditions apply"]
LOREM = ["Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
         "Sed do eiusmod tempor incididunt ut labore et dolore magna.",
         "Szczegóły zamówienia zostaną wysłane na podany adres e-mail."]

_uid = 0


def uid() -> str:
    global _uid
    _uid += 1
    return f"o{_uid}"


def color(lmin: int = 20, lmax: int = 85) -> tuple[str, int]:
    h, s, l = random.randint(0, 359), random.randint(25, 90), random.randint(lmin, lmax)
    return f"hsl({h},{s}%,{l}%)", l


def fg(l: int) -> str:
    return "#fff" if l < 58 else "#1a1a1a"


# ----------------------------- poprawne elementy -----------------------------

def ok_button() -> str:
    """Różne style przycisków: wypełniony, outline, ghost, ikonowy, <a> wyglądający jak przycisk."""
    bg, l = color()
    kind = random.choice(["fill", "fill", "outline", "outline", "ghost", "icon", "link_btn"])
    fs = random.randint(12, 20)
    r = random.randint(0, 12)
    pad = f"{random.randint(6, 14)}px {random.randint(12, 28)}px"
    if kind == "outline":
        c, _ = color(20, 50)
        st = f"background:transparent;color:{c};border:{random.choice([1, 2])}px solid {c}"
    elif kind == "ghost":
        st = "background:rgba(0,0,0,.07);color:#222;border:none"
    elif kind == "icon":
        s = random.randint(30, 44)
        pad = "0"
        st = (f"width:{s}px;height:{s}px;font-size:{random.randint(16, 24)}px;"
              f"background:{random.choice(['transparent', bg])};color:{random.choice(['#222', fg(l)])};"
              f"border:{random.choice(['none', '1px solid #999'])}")
        return f'<button data-c="0" style="{st};border-radius:{r}px;padding:{pad};font-family:inherit">{random.choice(["☰", "✕", "⋮", "+", "⚙", "←"])}</button>'
    else:
        st = f"background:{bg};color:{fg(l)};border:{random.choice(['none', '1px solid #333'])}"
    if kind == "link_btn":
        return (f'<a href="#" data-c="0" style="display:inline-block;text-decoration:none;{st};'
                f'border-radius:{r}px;padding:{pad};font-size:{fs}px">{random.choice(WORDS)}</a>')
    return (f'<button data-c="0" style="{st};border-radius:{r}px;padding:{pad};'
            f'font-size:{fs}px;font-family:inherit">{random.choice(WORDS)}</button>')


def ok_link() -> str:
    c, _ = color(20, 50)
    deco = random.choice(["underline", "underline", "none"])
    if random.random() < 0.25:
        c = "#6b7280"
    return (f'<a href="#" data-c="1" style="color:{c};font-size:{random.randint(13, 20)}px;'
            f'text-decoration:{deco}">{random.choice(WORDS)}</a>')


def ok_input() -> str:
    """Pole tekstowe: z ramką, z samym podkreśleniem (material), wypełnione, z etykietą nad polem."""
    kind = random.choice(["box", "box", "underline", "underline", "filled", "floating"])
    w, fs = random.randint(140, 280), random.randint(12, 18)
    ph = random.choice(WORDS)
    if kind == "box":
        st = f"padding:{random.randint(5, 12)}px;border:1px solid #888;border-radius:{random.randint(0, 8)}px"
    elif kind == "filled":
        st = f"padding:{random.randint(7, 12)}px;border:none;border-radius:{random.randint(0, 6)}px;background:#ececec"
    else:
        st = (f"padding:{random.randint(5, 9)}px 2px;border:none;border-bottom:1px solid "
              f"{random.choice(['#bbb', '#999', '#ddd'])};border-radius:0;background:transparent")
    inp = f'<input data-c="2" type="text" placeholder="{ph}" style="width:{w}px;{st};font-size:{fs}px;font-family:inherit;outline:none">'
    if kind == "floating":
        return (f'<div><div style="font-size:12px;color:#777;margin-bottom:2px">{ph}</div>{inp}</div>')
    return inp


def nav_row() -> str:
    """Menu: kilka linków obok siebie, bez podkreślenia."""
    c, _ = color(20, 50)
    items = "".join(
        f'<a href="#" data-c="1" style="color:{c};text-decoration:none;font-size:{random.randint(14, 18)}px;'
        f'margin-right:{random.randint(14, 30)}px">{w}</a>'
        for w in random.sample(WORDS, random.randint(3, 5)))
    return f'<div style="white-space:nowrap">{items}</div>'


def image_link() -> str:
    a, _ = color(40, 80)
    b, _ = color(40, 80)
    return (f'<a href="#" data-c="1" style="display:block;width:{random.randint(80, 160)}px;'
            f'height:{random.randint(60, 120)}px;background:linear-gradient({random.randint(0, 180)}deg,{a},{b});'
            f'border-radius:{random.randint(0, 8)}px"></a>')


def product_card() -> str:
    c, _ = color(20, 45)
    return (f'<div style="width:{random.randint(170, 240)}px;border:1px solid #ddd;border-radius:8px;'
            f'padding:10px;background:#fff;color:#222">{image_link()}'
            f'<div style="margin:8px 0 4px"><a href="#" data-c="1" style="color:{c};text-decoration:none;'
            f'font-weight:bold;font-size:15px">{random.choice(WORDS)}</a></div>'
            f'<div style="font-size:14px;margin-bottom:8px">${random.randint(5, 99)}.{random.randint(10, 99)}</div>'
            f'{ok_button()}</div>')


def login_form() -> str:
    return (f'<div style="width:{random.randint(240, 300)}px;padding:16px;background:#fff;'
            f'border:1px solid #e5e5e5;border-radius:8px;color:#222">'
            f'<div style="font-size:18px;margin-bottom:10px">{random.choice(["Login", "Zaloguj", "Checkout"])}</div>'
            f'<div style="margin-bottom:12px">{ok_input()}</div><div style="margin-bottom:12px">{ok_input()}</div>'
            f'{ok_button()}</div>')


def ok_checkbox() -> str:
    s = random.randint(14, 26)
    return (f'<label style="display:inline-flex;align-items:center;gap:8px;'
            f'font-size:{random.randint(13, 18)}px"><input data-c="3" type="checkbox" '
            f'style="width:{s}px;height:{s}px;margin:0"> {random.choice(WORDS)}</label>')


def ok_select() -> str:
    opts = "".join(f"<option>{w}</option>" for w in random.sample(WORDS, 3))
    look = random.choice(["", "border:1px solid #888;", "border:none;background:#ececec;border-radius:4px;",
                          "border:none;border-bottom:1px solid #999;background:transparent;"])
    return (f'<select data-c="4" style="{look}padding:{random.randint(5, 10)}px;'
            f'font-size:{random.randint(12, 18)}px;font-family:inherit">{opts}</select>')


def ok_text() -> str:
    return (f'<p style="max-width:{random.randint(180, 340)}px;margin:0;'
            f'font-size:{random.randint(13, 17)}px;color:#444">{random.choice(LOREM)}</p>')


# --------------------------------- bugi UI ----------------------------------

def bug_overflow_button() -> str:
    bg, l = color()
    return (f'<button data-c="7" data-bug="overflow" data-fb="0" style="width:{random.randint(50, 110)}px;'
            f'height:{random.randint(22, 40)}px;background:{bg};color:{fg(l)};border:none;'
            f'border-radius:4px;padding:0;overflow:visible;white-space:nowrap;'
            f'font-size:{random.randint(28, 52)}px;font-weight:bold;font-family:inherit">'
            f'{random.choice(WORDS[:6])}</button>')


def bug_overflow_div() -> str:
    bg, l = color(55, 90)
    return (f'<div data-c="7" data-bug="overflow" style="width:{random.randint(120, 220)}px;'
            f'padding:6px;border:2px solid #333;background:{bg};color:{fg(l)};'
            f'white-space:nowrap;font-size:{random.randint(16, 26)}px">{random.choice(LONG)}</div>')


def bug_clip() -> str:
    bg, l = color(55, 90)
    return (f'<div data-c="6" data-bug="clip" style="width:{random.randint(140, 260)}px;'
            f'height:{random.randint(30, 60)}px;overflow:hidden;background:{bg};border:2px solid #333">'
            f'<div style="font-size:{random.randint(24, 44)}px;white-space:nowrap;color:{fg(l)}">'
            f'{random.choice(LONG)}</div></div>')


def bug_overlap_abs() -> str:
    i = uid()
    a, la = color(25, 60)
    b, lb = color(25, 60)
    return (f'<div style="position:relative;width:300px;height:130px">'
            f'<div data-ovl="{i}" style="position:absolute;top:0;left:0;z-index:2;background:{a};'
            f'color:{fg(la)};padding:8px 16px;font-size:{random.randint(20, 30)}px">Etykieta</div>'
            f'<div data-ovl="{i}" style="position:absolute;top:{random.randint(8, 30)}px;'
            f'left:{random.randint(30, 110)}px;width:180px;height:80px;z-index:1;background:{b};'
            f'color:{fg(lb)};padding:8px">Pudełko pod spodem</div></div>')


def bug_overlap_stack() -> str:
    i = uid()
    a, la = color(30, 70)
    b, lb = color(30, 70)
    return (f'<div style="width:{random.randint(200, 300)}px">'
            f'<div data-ovl="{i}" style="background:{a};color:{fg(la)};padding:20px">Blok A</div>'
            f'<div data-ovl="{i}" style="position:relative;background:{b};color:{fg(lb)};'
            f'padding:20px;margin-top:-{random.randint(18, 40)}px">Blok B nachodzi na A</div></div>')


# ------------------------------- okno modalne --------------------------------

def modal_block() -> str:
    """Przyciemnione tło (nie przechwytuje myszy) + okno dialogowe na środku."""
    w = random.randint(300, 520)
    h = random.randint(190, 320)
    dx, dy = random.randint(-80, 80), random.randint(-60, 60)
    hb, lh = color(10, 35) if random.random() < 0.5 else color(40, 80)
    body_bg = random.choice(["#fff", "#f1f2f4", "#fafafa", "#20242b"])
    body_fg = "#eee" if body_bg == "#20242b" else "#222"
    btn_bg, bl = color(30, 60)
    close = (f'<button data-c="0" style="background:{btn_bg};color:{fg(bl)};border:none;'
             f'border-radius:{random.randint(0, 10)}px;padding:8px 20px;'
             f'font-size:{random.randint(13, 17)}px">{random.choice(["Close", "OK", "Zamknij", "Zapisz"])}</button>'
             if random.random() < 0.6 else
             f'<a href="#" data-c="1" style="color:{body_fg};font-size:{random.randint(13, 17)}px;'
             f'text-decoration:underline">{random.choice(["Close", "Zamknij", "Nie, dziękuję"])}</a>')
    return (
        f'<div style="position:fixed;inset:0;background:rgba(0,0,0,{random.uniform(0.35, 0.65):.2f});'
        f'pointer-events:none;z-index:50"></div>'
        f'<div data-c="5" data-modal="1" style="position:fixed;z-index:60;left:calc(50% - {w // 2}px + {dx}px);'
        f'top:calc(50% - {h // 2}px + {dy}px);width:{w}px;height:{h}px;background:{body_bg};'
        f'color:{body_fg};border-radius:{random.randint(0, 12)}px;overflow:hidden;'
        f'display:flex;flex-direction:column;box-shadow:0 8px 30px rgba(0,0,0,.4)">'
        f'<div style="background:{hb};color:{fg(lh)};padding:14px 18px;font-weight:bold;'
        f'font-size:{random.randint(15, 20)}px">{random.choice(["Newsletter", "Cookies", "Potwierdzenie", "Special offer", "Zaloguj się"])}</div>'
        f'<div style="padding:16px 18px;flex:1;font-size:{random.randint(13, 16)}px">{random.choice(LOREM)}</div>'
        f'<div style="padding:12px 18px;text-align:center">{close}</div></div>'
    )


OK_BLOCKS = [ok_button, ok_button, ok_link, ok_input, ok_input, ok_checkbox, ok_select, ok_text,
             nav_row, image_link, product_card, login_form]
BUG_BLOCKS = [bug_overflow_button, bug_overflow_div, bug_clip, bug_overlap_abs, bug_overlap_stack]


def build_page() -> str:
    bg, l = color(88, 99) if random.random() < 0.8 else color(8, 20)
    text = "#111" if l > 50 else "#eee"
    cells = []
    for _ in range(random.randint(6, 14)):
        block = random.choice(BUG_BLOCKS if random.random() < 0.45 else OK_BLOCKS)()
        cells.append(f'<div style="padding:12px 70px 40px 12px">{block}</div>')
    if random.random() < 0.18:
        cells.append(modal_block())
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        "html,body{margin:0;height:100%;overflow:hidden}"
        f"body{{display:flex;flex-wrap:wrap;align-items:flex-start;gap:{random.randint(10, 40)}px;"
        f"padding:{random.randint(16, 40)}px;background:{bg};color:{text};"
        f"font-family:{random.choice(FONTS)}}}"
        "</style></head><body>" + "".join(cells) + "</body></html>"
    )


EXTRACT_JS = """
() => {
  const W = innerWidth, H = innerHeight, out = [];
  const norm = r => ({l: r.left, t: r.top, r: r.right, b: r.bottom});
  const push = (c, r) => {
    const a = (r.r - r.l) * (r.b - r.t);
    const l = Math.max(0, r.l), t = Math.max(0, r.t), rr = Math.min(W, r.r), b = Math.min(H, r.b);
    const w = rr - l, h = b - t;
    if (a <= 0 || w < 6 || h < 6 || (w * h) / a < 0.7) return;
    out.push([c, (l + w / 2) / W, (t + h / 2) / H, w / W, h / H]);
  };
  const textRect = el => { const g = document.createRange(); g.selectNodeContents(el); return g.getBoundingClientRect(); };
  // Gdy na stronie jest modal, pomijamy elementy zasłonięte przez okno dialogowe.
  const hasModal = !!document.querySelector('[data-modal]');
  const visibleAt = (x, y, els) => {
    if (!hasModal) return true;
    const e = document.elementFromPoint(x, y);
    return !!e && els.some(n => n.contains(e) || e.contains(n));
  };
  document.querySelectorAll('[data-c]').forEach(el => {
    const bug = el.dataset.bug, b = el.getBoundingClientRect();
    if (!visibleAt(b.left + b.width / 2, b.top + b.height / 2, [el])) return;
    if (!bug) { push(+el.dataset.c, norm(b)); return; }
    if (bug === 'overflow') {
      const t = textRect(el);
      if (t.width > b.width * 1.15 || t.height > b.height * 1.15) {
        push(+el.dataset.c, {l: Math.min(b.left, t.left), t: Math.min(b.top, t.top),
                             r: Math.max(b.right, t.right), b: Math.max(b.bottom, t.bottom)});
      } else if (el.dataset.fb) push(+el.dataset.fb, norm(b));
    } else if (bug === 'clip') {
      if (el.scrollWidth > el.clientWidth + 4 || el.scrollHeight > el.clientHeight + 4) push(+el.dataset.c, norm(b));
    }
  });
  const groups = {};
  document.querySelectorAll('[data-ovl]').forEach(el => { (groups[el.dataset.ovl] = groups[el.dataset.ovl] || []).push(el); });
  Object.values(groups).forEach(g => {
    const a = g[0].getBoundingClientRect(), b = g[1].getBoundingClientRect();
    const l = Math.max(a.left, b.left), t = Math.max(a.top, b.top);
    const r = Math.min(a.right, b.right), bt = Math.min(a.bottom, b.bottom);
    if (r - l > 12 && bt - t > 12 && visibleAt((l + r) / 2, (t + bt) / 2, g)) push(8, {l, t, r, b: bt});
  });
  return out;
}
"""


def write_yaml(root: Path) -> Path:
    path = root / "dataset_ui.yaml"
    # Ultralytics rozwiązuje "path: ." względem bieżącego katalogu (nie pliku YAML),
    # dlatego zapisujemy ścieżkę bezwzględną.
    lines = [f"path: {root.resolve()}", "train: images/train", "val: images/val", f"nc: {len(NAMES)}",
             "names: [" + ", ".join(f'"{n}"' for n in NAMES) + "]"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Generator zrzutów z bugami UI (YOLO)")
    ap.add_argument("--root", type=Path, default=Path("dataset"), help="katalog paczki (images/, labels/)")
    ap.add_argument("--count", type=int, default=800)
    ap.add_argument("--val-ratio", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    random.seed(args.seed)
    for split in ("train", "val"):
        (args.root / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.root / "labels" / split).mkdir(parents=True, exist_ok=True)

    stats: Counter[str] = Counter()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        for n in range(args.count):
            vw, vh = random.choice(VIEWPORTS)
            page.set_viewport_size({"width": vw, "height": vh})
            page.set_content(build_page())
            boxes = page.evaluate(EXTRACT_JS)
            split = "val" if random.random() < args.val_ratio else "train"
            stem = f"gen_{args.seed}_{n:05d}"
            page.screenshot(path=str(args.root / "images" / split / f"{stem}.png"))
            with (args.root / "labels" / split / f"{stem}.txt").open("w") as fh:
                for c, x, y, w, h in boxes:
                    fh.write(f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
                    stats[NAMES[c]] += 1
            if (n + 1) % 50 == 0:
                print(f"{n + 1}/{args.count}")
        browser.close()

    yaml_path = write_yaml(args.root)
    print("Gotowe. Etykiety:", dict(stats))
    print("YAML:", yaml_path)


if __name__ == "__main__":
    main()
