"""Zbieranie zrzutów i etykiet z PRAWDZIWYCH stron (Playwright) w numeracji dataset_ui.yaml.

Klasy (te same co w gen_dataset.py i dataset_ui.yaml):
    0 button, 1 link, 2 input, 3 checkbox, 4 select, 5 ui_modal,
    6 bug_clipping, 7 bug_text_overflow, 8 bug_overlap

Wynik trafia do OSOBNEGO katalogu (domyślnie dataset_real) i służy jako ZBIÓR TESTOWY:
    dataset_real/images/val, dataset_real/labels/val, dataset_real/dataset_real.yaml
Bugi (klasy 6-8) NIE są wpisywane do etykiet. Reguły DOM tylko je podpowiadają:
    dataset_real/suggested_bugs/<nazwa>.txt  (do ręcznego przejrzenia)

Użycie:
    python collect_real.py --urls urls.txt
    python collect_real.py --urls urls.txt --saucedemo      # dodatkowo konto visual_user

    # TRYB WSADOWY (zbiór do uczenia): 8 podstron na domenę, 2 zrzuty na stronę,
    # 25% domen do testu (val), reszta do train; przerwy 3-8 s, szanuje robots.txt:
    python collect_real.py --urls urls_train.txt --root dataset_real_big --crawl 8 --scrolls 2 --test-frac 0.25
    # Skrypt przy blokadzie (403/429/captcha) kończy z domeną i niczego nie obchodzi.
    # ocena modelu na prawdziwych stronach:
    #   yolo detect val model=yolov8_ui_bugs.pt data=dataset_real/dataset_real.yaml imgsz=1280

Plik urls.txt: jedna strona na linię, "nazwa pełny_adres" (# = komentarz), np.
    entry_ad   <PEŁNY adres skopiowany z paska przeglądarki>
    lokalny    file:///home/uzytkownik/Pulpit/testy/test.html
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from playwright.sync_api import sync_playwright

NAMES = ["button", "link", "input", "checkbox", "select", "ui_modal",
         "bug_clipping", "bug_text_overflow", "bug_overlap"]

SELECTORS = [
    (0, "button, input[type='submit'], input[type='button'], input[type='reset'], "
        "[role='button'], a.btn, a.button"),
    (1, "a[href]:not(.btn):not(.button):not([role='button'])"),
    (2, "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='reset'])"
        ":not([type='checkbox']):not([type='radio']):not([type='image']):not([type='file']), textarea"),
    (3, "input[type='checkbox']"),
    (4, "select"),
    (5, "[role='dialog'], [aria-modal='true'], #modal, .modal.show, "
        ".modal[style*='display: block'], .popup"),
]

EXTRACT_JS = """
(selectors) => {
  const W = innerWidth, H = innerHeight, out = [];
  const visible = el => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 4 && r.height > 4;
  };
  const iou = (a, b) => {
    const l = Math.max(a[0], b[0]), t = Math.max(a[1], b[1]);
    const r = Math.min(a[2], b[2]), bt = Math.min(a[3], b[3]);
    const i = Math.max(0, r - l) * Math.max(0, bt - t);
    const u = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i;
    return u > 0 ? i / u : 0;
  };
  // Przyciemnione tło modala (duży element fixed/absolute bez własnego tekstu) traktujemy jak przezroczyste,
  // żeby elementy pod nim były nadal etykietowane (zasłania je tylko samo okno dialogowe).
  const isBackdrop = n => {
    if (n === document.documentElement || n === document.body) return false;
    const s = getComputedStyle(n);
    if (s.position !== 'fixed' && s.position !== 'absolute') return false;
    const r = n.getBoundingClientRect();
    return r.width >= W * 0.9 && r.height >= H * 0.9;
  };
  const topAt = (x, y) => {
    for (const n of document.elementsFromPoint(x, y)) { if (!isBackdrop(n)) return n; }
    return null;
  };
  const seen = [];
  for (const [c, sel] of selectors) {
    for (const el of document.querySelectorAll(sel)) {
      if (!visible(el)) continue;
      const r = el.getBoundingClientRect();
      const l = Math.max(0, r.left), t = Math.max(0, r.top);
      const rr = Math.min(W, r.right), b = Math.min(H, r.bottom);
      const w = rr - l, h = b - t;
      if (w < 6 || h < 6 || (w * h) / (r.width * r.height) < 0.6) continue;
      // pomijamy elementy zasłonięte przez inne (np. przez okno modalne)
      const e = topAt(l + w / 2, t + h / 2);
      if (!e || !(el.contains(e) || e.contains(el))) continue;
      const box = [l, t, rr, b];
      if (seen.some(s => s[0] === c && iou(s[1], box) > 0.85)) continue;   // duplikaty
      seen.push([c, box]);
      out.push([c, (l + w / 2) / W, (t + h / 2) / H, w / W, h / H]);
    }
  }
  return out;
}
"""

# Podpowiedzi bugów z reguł DOM (tylko do przeglądu, nie do etykiet)
BUG_HINTS_JS = """
() => {
  const W = innerWidth, H = innerHeight, out = [];
  const add = (c, r) => {
    const l = Math.max(0, r.left), t = Math.max(0, r.top);
    const rr = Math.min(W, r.right), b = Math.min(H, r.bottom);
    if (rr - l < 6 || b - t < 6) return;
    out.push([c, (l + rr) / 2 / W, (t + b) / 2 / H, (rr - l) / W, (b - t) / H]);
  };
  for (const el of document.querySelectorAll('body *')) {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasText) continue;
    const g = document.createRange(); g.selectNodeContents(el);
    const t = g.getBoundingClientRect();
    // ucięcie: tekst wychodzi poza przodka z overflow: hidden/clip
    let clipped = null;
    for (let a = el, i = 0; a && a !== document.body && i < 4; a = a.parentElement, i++) {
      const as = getComputedStyle(a);
      if (['hidden', 'clip'].includes(as.overflowX) || ['hidden', 'clip'].includes(as.overflowY)) {
        const ar = a.getBoundingClientRect();
        if (t.right > ar.right + 4 || t.bottom > ar.bottom + 4) { clipped = ar; break; }
      }
    }
    if (clipped) { add(6, clipped); continue; }
    if (s.overflowX === 'visible' && t.width > r.width * 1.15 + 4) {
      add(7, {left: Math.min(r.left, t.left), top: Math.min(r.top, t.top),
              right: Math.max(r.right, t.right), bottom: Math.max(r.bottom, t.bottom)});
    }
  }
  return out;
}
"""


def capture(page, root: Path, stem: str, stats: Counter, settle_ms: int = 800,
            split: str = "val", scroll_y: int = 0, min_labels: int = 0) -> int:
    """Zrzut bieżącego widoku + etykiety z DOM. Zwraca liczbę zapisanych ramek (0 = pominięto)."""
    if scroll_y:
        page.evaluate("y => window.scrollTo(0, y)", scroll_y)
    page.wait_for_timeout(settle_ms)
    boxes = page.evaluate(EXTRACT_JS, [[c, s] for c, s in SELECTORS])
    if len(boxes) < min_labels:
        print(f"[POMIJAM] {stem}: tylko {len(boxes)} etykiet (< {min_labels})")
        return 0
    hints = page.evaluate(BUG_HINTS_JS)

    (root / "images" / split).mkdir(parents=True, exist_ok=True)
    (root / "labels" / split).mkdir(parents=True, exist_ok=True)
    (root / "suggested_bugs").mkdir(parents=True, exist_ok=True)

    page.screenshot(path=str(root / "images" / split / f"{stem}.png"), full_page=False)
    with (root / "labels" / split / f"{stem}.txt").open("w", encoding="utf-8") as fh:
        for c, x, y, w, h in boxes:
            fh.write(f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
            stats[NAMES[c]] += 1
    with (root / "suggested_bugs" / f"{stem}.txt").open("w", encoding="utf-8") as fh:
        for c, x, y, w, h in hints:
            fh.write(f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
    print(f"[OK] {split}/{stem}: etykiet {len(boxes)}, podpowiedzi bugów {len(hints)}")
    return len(boxes)


# ------------------------- uprzejme crawlowanie (robots, opóźnienia) -------------------------

SKIP_WORDS = ("logout", "signout", "sign_out", "delete", "remove", "unsubscribe", "download",
              "mailto:", "tel:", "javascript:")
SKIP_EXT = (".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".exe", ".dmg", ".xml")
BLOCK_MARKERS = ("captcha", "access denied", "are you a robot", "unusual traffic", "too many requests",
                 "verify you are human", "just a moment")


class Robots:
    """robots.txt per domena. Nie da się pobrać -> zakładamy 'wolno'; 401/403 -> zakaz (jak w standardzie)."""

    def __init__(self) -> None:
        self.cache: dict[str, RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.cache:
            rp = RobotFileParser()
            try:
                with urlopen(Request(base + "/robots.txt", headers={"User-Agent": "bug-ai-collector"}),
                             timeout=10) as r:
                    rp.parse(r.read().decode("utf-8", "ignore").splitlines())
                self.cache[base] = rp
            except HTTPError as e:
                if e.code in (401, 403):
                    rp.parse(["User-agent: *", "Disallow: /"])
                    self.cache[base] = rp
                else:
                    self.cache[base] = None
            except Exception:
                self.cache[base] = None
        rp = self.cache[base]
        return True if rp is None else rp.can_fetch("*", url)


def bare(host: str) -> str:
    return host.lower().removeprefix("www.")


def internal_links(page, limit: int) -> list[str]:
    """Losowe wewnętrzne linki z bieżącej strony (ta sama domena, bez wylogowań/pobrań)."""
    here = urlparse(page.url)
    hrefs = page.evaluate("() => [...document.querySelectorAll('a[href]')].map(a => a.href)")
    seen, out = {page.url.split("#")[0]}, []
    for h in hrefs:
        h = h.split("#")[0]
        u = urlparse(h)
        if (u.scheme not in ("http", "https") or bare(u.netloc) != bare(here.netloc) or h in seen
                or h.lower().endswith(SKIP_EXT) or any(w in h.lower() for w in SKIP_WORDS)):
            continue
        seen.add(h)
        out.append(h)
    random.shuffle(out)
    return out[:limit]


def is_blocked(resp, page) -> bool:
    """Strona nas odrzuca (status/captcha). W takim wypadku kończymy z domeną, niczego nie obchodzimy."""
    if resp is not None and resp.status in (401, 403, 429, 503):
        return True
    try:
        head = (page.title() + " " + page.inner_text("body")[:400]).lower()
    except Exception:
        return False
    return any(m in head for m in BLOCK_MARKERS)


def split_for(url: str, test_frac: float) -> str:
    """Stały podział po domenie: ta sama domena zawsze trafia do tego samego zbioru (brak przecieku)."""
    dom = bare(urlparse(url).netloc)
    return "val" if int(hashlib.md5(dom.encode()).hexdigest(), 16) % 100 < test_frac * 100 else "train"


def scroll_positions(page, scrolls: int) -> list[int]:
    if scrolls <= 1:
        return [0]
    total = page.evaluate("document.documentElement.scrollHeight")
    vh = page.evaluate("innerHeight")
    pos = [0]
    for k in range(1, scrolls):
        y = int(k * vh * 0.9)
        if y < total - vh * 0.3:
            pos.append(y)
    return pos


def read_urls(path: Path) -> list[tuple[str, str]]:
    """Linia: 'nazwa adres'. Adres to OSTATNI element linii, więc nazwa może mieć spacje.
    Adres bez schematu (np. www.allegro.pl) dostaje https://."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = line.split()
        url = tokens[-1]
        if not url.startswith(("http://", "https://", "file://")):
            if "." in url and "/" not in url[:2]:
                url = "https://" + url
            else:
                print(f"[POMIJAM] zły adres w linii: {line!r}")
                continue
        name = "_".join(tokens[:-1]) or url.split("//", 1)[-1]
        name = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_").lower()[:60]
        rows.append((name, url))
    return rows


def saucedemo_flow(page, root: Path, stats: Counter) -> None:
    """Konto visual_user (login i hasło są wyświetlane na samej stronie demo)."""
    base = "https://www.saucedemo.com/"
    steps = [("saucedemo_login", None)]
    page.goto(base, wait_until="networkidle", timeout=20000)
    capture(page, root, "saucedemo_login", stats)
    page.fill("#user-name", "visual_user")
    page.fill("#password", "secret_sauce")
    page.click("#login-button")
    page.wait_for_url("**/inventory.html", timeout=15000)
    capture(page, root, "saucedemo_visual_inventory", stats)
    page.locator(".inventory_item_name").first.click()
    capture(page, root, "saucedemo_visual_item", stats)
    page.locator("button:has-text('Add to cart')").first.click()
    page.click(".shopping_cart_link")
    capture(page, root, "saucedemo_visual_cart", stats)
    page.click("#checkout")
    capture(page, root, "saucedemo_visual_checkout", stats)


def write_yaml(root: Path) -> None:
    has_train = any((root / "images" / "train").glob("*.png"))
    lines = [f"path: {root.resolve()}", f"train: images/{'train' if has_train else 'val'}", "val: images/val",
             f"nc: {len(NAMES)}", "names:"] + [f"  {i}: {n}" for i, n in enumerate(NAMES)]
    (root / "dataset_real.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def crawl_domain(page, args, robots: Robots, name: str, url: str, stats: Counter) -> None:
    """Strona startowa + do --crawl wewnętrznych podstron, każda w kilku pozycjach przewinięcia."""
    split = split_for(url, args.test_frac)
    if args.respect_robots and not robots.allowed(url):
        print(f"[ROBOTS] {url}: zabronione w robots.txt, pomijam")
        return
    resp = page.goto(url, wait_until=args.wait_until, timeout=20000)
    if is_blocked(resp, page):
        print(f"[BLOKADA] {url}: strona nas odrzuca, kończę z tą domeną (niczego nie obchodzę)")
        return

    queue = [url] + internal_links(page, args.crawl)
    for i, link in enumerate(queue):
        try:
            if i:
                time.sleep(random.uniform(args.delay_min, args.delay_max))
                if args.respect_robots and not robots.allowed(link):
                    print(f"[ROBOTS] {link}: pomijam")
                    continue
                resp = page.goto(link, wait_until=args.wait_until, timeout=20000)
                if is_blocked(resp, page):
                    print(f"[BLOKADA] {link}: kończę z domeną {name}")
                    return
            stem0 = f"real_{name}" + (f"_p{i:02d}" if i else "")
            for k, y in enumerate(scroll_positions(page, args.scrolls)):
                capture(page, args.root, stem0 + (f"_s{k}" if k else ""), stats, settle_ms=args.settle,
                        split=split, scroll_y=y, min_labels=args.min_labels)
        except Exception as exc:
            print(f"[BŁĄD] {link}: {exc}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Zrzuty i etykiety z prawdziwych stron (test lub trening)")
    ap.add_argument("--urls", type=Path, help="plik z listą 'nazwa adres'")
    ap.add_argument("--root", type=Path, default=Path("dataset_real"))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--saucedemo", action="store_true", help="dodaj scenariusz visual_user")
    ap.add_argument("--wait-until", default="networkidle",
                    choices=["load", "domcontentloaded", "networkidle"],
                    help="kiedy uznać stronę za załadowaną (dla aplikacji z websocketami użyj domcontentloaded)")
    ap.add_argument("--settle", type=int, default=800,
                    help="ms oczekiwania po załadowaniu (animacje, hydratacja SPA)")
    ap.add_argument("--crawl", type=int, default=0,
                    help="ile wewnętrznych podstron dodać do każdej strony startowej (0 = tylko strona z listy)")
    ap.add_argument("--scrolls", type=int, default=1,
                    help="ile zrzutów na stronę (kolejne przewinięcia o ~1 ekran)")
    ap.add_argument("--test-frac", type=float, default=1.0,
                    help="ułamek DOMEN do zbioru testowego val (1.0 = wszystko do val, jak dotąd; "
                         "np. 0.25 = 25%% domen do val, reszta do train)")
    ap.add_argument("--delay-min", type=float, default=3.0, help="min. przerwa między stronami [s]")
    ap.add_argument("--delay-max", type=float, default=8.0, help="maks. przerwa między stronami [s]")
    ap.add_argument("--min-labels", type=int, default=3, help="pomiń zrzuty z mniejszą liczbą etykiet")
    ap.add_argument("--no-robots", dest="respect_robots", action="store_false",
                    help="nie sprawdzaj robots.txt (domyślnie sprawdzamy)")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    if not args.urls and not args.saucedemo:
        ap.error("podaj --urls urls.txt i/lub --saucedemo")

    random.seed(args.seed)
    stats: Counter[str] = Counter()
    robots = Robots()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": args.width, "height": args.height},
                                  device_scale_factor=1)
        page = ctx.new_page()

        if args.urls:
            rows = read_urls(args.urls)
            random.shuffle(rows)          # losowa kolejność = mniej uderzeń w jedną domenę pod rząd
            for n, (name, url) in enumerate(rows):
                if n:
                    time.sleep(random.uniform(args.delay_min, args.delay_max))
                try:
                    crawl_domain(page, args, robots, name, url, stats)
                except Exception as exc:
                    print(f"[BŁĄD] {url}: {exc}")
        if args.saucedemo:
            try:
                saucedemo_flow(page, args.root, stats)
            except Exception as exc:
                print(f"[BŁĄD] scenariusz saucedemo: {exc}")
        browser.close()

    write_yaml(args.root)
    n_tr = len(list((args.root / "images" / "train").glob("*.png")))
    n_va = len(list((args.root / "images" / "val").glob("*.png")))
    print(f"\nObrazów: train {n_tr}, val {n_va}")
    print("Podsumowanie etykiet:", json.dumps(dict(stats), ensure_ascii=False))
    print("YAML:", args.root / "dataset_real.yaml")


if __name__ == "__main__":
    main()
