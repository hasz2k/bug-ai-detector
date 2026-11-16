from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ultralytics import YOLO

log = logging.getLogger("export")


def _detect_backend() -> str:
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "rocm" if torch.version.hip is not None else "cuda"
    return "cpu"


def _validate_imgsz(imgsz: int) -> int:
    if imgsz <= 0 or imgsz % 32 != 0:
        raise ValueError(
            f"imgsz={imgsz} jest nieprawidłowy — musi być dodatnią wielokrotnością 32 "
            f"(np. 320, 416, 640, 1280)."
        )
    return imgsz


def export_model(
    weights_path: Path | str = "yolov8_ui_bugs.pt",
    imgsz: int = 640,
    half: bool = True,
    target_format: str = "onnx",
    workspace_gib: int = 4,
    device: str = "0",
) -> Path:
    weights = Path(weights_path).expanduser().resolve()
    if not weights.is_file():
        raise FileNotFoundError(f"Nie znaleziono wag modelu: {weights}")

    imgsz = _validate_imgsz(imgsz)

    if target_format not in {"onnx", "engine"}:
        raise ValueError(f"Nieobsługiwany format: {target_format!r} (dozwolone: onnx, engine)")

    backend = _detect_backend()
    log.info("Wykryty backend: %s", backend)

    if backend == "cpu":
        if target_format == "engine":
            raise RuntimeError(
                "TensorRT (.engine) wymaga GPU NVIDIA. Na CPU dostępny jest tylko format ONNX."
            )
        if half:
            log.warning("CPU nie obsługuje FP16 — przełączam half=False.")
            half = False
        device = "cpu"
    else:
        device = device

    log.info(
        "Eksport → format=%s imgsz=%d half=%s device=%s backend=%s",
        target_format, imgsz, half, device, backend,
    )

    log.info("Ładowanie modelu: %s", weights)
    model = YOLO(str(weights))

    try:
        if target_format == "onnx":
            exported = model.export(
                format="onnx",
                imgsz=imgsz,
                half=half,
                simplify=True,
                opset=17,
                dynamic=False,
                device=device,
            )
        else:
            exported = model.export(
                format="engine",
                imgsz=imgsz,
                half=half,
                workspace=workspace_gib,
                device=device,
            )
    except Exception as e:
        raise RuntimeError(f"Eksport do {target_format} nie powiódł się: {e}") from e

    if not exported:
        raise RuntimeError("Ultralytics nie zwrócił ścieżki do wyeksportowanego modelu.")

    out = Path(exported).resolve()
    log.info("Gotowe: %s (%.1f MiB)", out, out.stat().st_size / 1024**2)
    return out


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Eksport modelu UI YOLOv8 do ONNX / TensorRT",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--weights", type=Path, default=Path("yolov8_ui_bugs.pt"))
    p.add_argument("--format", choices=("onnx", "engine"), default="onnx")
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--fp32", action="store_true")
    p.add_argument("--workspace", type=int, default=4, metavar="GiB")
    p.add_argument("--device", default="0")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        out = export_model(
            weights_path=args.weights,
            imgsz=args.imgsz,
            half=not args.fp32,
            target_format=args.format,
            workspace_gib=args.workspace,
            device=args.device,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        log.error("%s", e)
        return 1

    print(f"Wyeksportowano zoptymalizowany model do: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
