"""Dołącza prawdziwe strony (dataset_real_big/images/train) do zbioru uczącego z zrównoważeniem klas.

Po co: strony typu dokumentacja/Wikipedia mają tysiące linków i mało pól/selectów/modali.
Bez korekty model uczy się wszędzie widzieć linki. Skrypt:
  * ogranicza liczbę zrzutów na domenę (--max-per-domain), najpierw zostawiając te z rzadkimi klasami,
  * odrzuca zrzuty zdominowane przez linki (>--link-max-share), jeśli nie ma w nich input/checkbox/select/modal,
  * powiela zrzuty z rzadkimi klasami (--oversample razy łącznie),
  * jest idempotentny: przy ponownym uruchomieniu najpierw usuwa swoje wcześniejsze pliki real_* z celu.
Zbiór testowy (images/val) NIE jest dotykany - nie trafia do uczenia.

Użycie:
    python merge_real.py --real dataset_real_big --target ~/Pulpit/testy/ui_elements_yolo
"""

from __future__ import annotations

import argparse
import random
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

NAMES = ["button", "link", "input", "checkbox", "select", "ui_modal",
         "bug_clipping", "bug_text_overflow", "bug_overlap"]
RARE = {2, 3, 4, 5}      # input, checkbox, select, ui_modal


def read_classes(label: Path) -> list[int]:
    return [int(l.split()[0]) for l in label.read_text().splitlines() if l.strip()]


def domain_key(stem: str) -> str:
    return re.sub(r"(_p\d+)?(_s\d+)?$", "", stem)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", type=Path, required=True, help="katalog z collect_real.py")
    ap.add_argument("--target", type=Path, required=True, help="katalog zbioru uczącego (ui_elements_yolo)")
    ap.add_argument("--max-per-domain", type=int, default=20)
    ap.add_argument("--link-max-share", type=float, default=0.7)
    ap.add_argument("--oversample", type=int, default=2, help="łączna liczba kopii zrzutu z rzadką klasą")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    random.seed(args.seed)

    src_img, src_lbl = args.real / "images" / "train", args.real / "labels" / "train"
    dst_img, dst_lbl = args.target / "images" / "train", args.target / "labels" / "train"
    assert src_img.exists(), f"Brak {src_img}"
    assert dst_img.exists(), f"Brak {dst_img}: wskaż katalog zbioru uczącego"

    for d in (dst_img, dst_lbl):                      # idempotencja
        for f in d.glob("real_*"):
            f.unlink()

    groups: dict[str, list[tuple[Path, list[int]]]] = defaultdict(list)
    for img in sorted(src_img.glob("*.png")):
        lbl = src_lbl / f"{img.stem}.txt"
        if not lbl.exists():
            continue
        groups[domain_key(img.stem)].append((img, read_classes(lbl)))

    before, after = Counter(), Counter()
    kept = dropped = copies = 0
    for key, items in groups.items():
        for _, cl in items:
            before.update(NAMES[c] for c in cl)
        good = []
        for img, cl in items:
            link_share = cl.count(1) / len(cl) if cl else 1.0
            if link_share > args.link_max_share and not (set(cl) & RARE):
                dropped += 1
                continue
            good.append((img, cl))
        good.sort(key=lambda t: (-len(set(t[1]) & RARE), random.random()))
        dropped += max(0, len(good) - args.max_per_domain)
        for img, cl in good[:args.max_per_domain]:
            n_copies = args.oversample if set(cl) & RARE else 1
            for k in range(n_copies):
                stem = img.stem + (f"_dup{k}" if k else "")
                shutil.copy(img, dst_img / f"{stem}.png")
                shutil.copy(src_lbl / f"{img.stem}.txt", dst_lbl / f"{stem}.txt")
                after.update(NAMES[c] for c in cl)
                copies += 1
            kept += 1

    print(f"Domen: {len(groups)} | zrzutów użytych: {kept} | odrzuconych: {dropped} | plików dodanych: {copies}")
    print("Etykiety w źródle  :", dict(before))
    print("Etykiety dodane    :", dict(after))


if __name__ == "__main__":
    main()
