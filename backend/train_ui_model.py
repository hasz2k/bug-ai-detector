"""Bug AI Detector Engine — pipeline treningowy YOLO dla UI QA (Python 3.10+).

Użycie:
    python train_ui_model.py                        # auto-detekcja akceleratora
    python train_ui_model.py --device cuda          # NVIDIA
    python train_ui_model.py --device rocm          # AMD (Linux/CachyOS)
    python train_ui_model.py --device 0,1           # konkretne GPU
    python train_ui_model.py --epochs 50 --batch 8 --cache --export onnx
    python train_ui_model.py --base-model runs/ui/<run>/weights/last.pt --resume
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import torch
    import yaml
    from ultralytics import YOLO
except ImportError as exc:
    sys.stderr.write(
        f"Brak wymaganej zależności: {exc.name}\n"
        "Zainstaluj: pip install --upgrade ultralytics torch pyyaml\n"
    )
    raise SystemExit(1) from exc

LOG = logging.getLogger("bugai.train")

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_YAML = PROJECT_ROOT / "dataset_ui.yaml"
DEFAULT_BASE_MODEL = "yolov8n.pt"
DEFAULT_PROJECT = PROJECT_ROOT / "runs" / "ui"
DEFAULT_RUN_NAME = "bug_ai_ui_model"
DEFAULT_WORKERS = 4

BACKENDS = ("auto", "cuda", "rocm", "mps", "cpu")
GPU_BACKENDS = ("cuda", "rocm")
GPU_IDS_PATTERN = re.compile(r"\d+(,\d+)*")
SUPPORTED_EXPORTS = ("coreml", "engine", "onnx", "openvino", "torchscript")
MIN_IMGSZ = 32

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_EXPORT_FAILED = 3
EXIT_INTERRUPTED = 130


class ConfigError(ValueError):
    """Wyjątek rzucany w przypadku błędnej konfiguracji parametrów."""


@dataclass(frozen=True, slots=True)
class TrainingConfig:
    dataset_yaml: Path
    base_model: str
    project: Path
    run_name: str
    epochs: int = 100
    imgsz: int = 640
    batch: int = 16
    device: str = "auto"
    workers: int | None = None
    optimizer: str = "AdamW"
    lr0: float = 1e-3
    patience: int = 30
    close_mosaic: int = 10
    seed: int = 42
    cache: bool = False
    resume: bool = False
    export_format: str | None = None

    @property
    def run_dir(self) -> Path:
        return self.project / self.run_name

    def validate(self) -> None:
        errors: list[str] = []

        if not self.dataset_yaml.is_file():
            errors.append(f"Dataset YAML nie istnieje: {self.dataset_yaml}")
        if self.epochs < 1:
            errors.append(f"epochs musi być >= 1 (jest {self.epochs})")
        if self.imgsz < MIN_IMGSZ or self.imgsz % MIN_IMGSZ != 0:
            errors.append(f"imgsz musi być wielokrotnością {MIN_IMGSZ} (jest {self.imgsz})")
        if self.batch < 1:
            errors.append(f"batch musi być >= 1 (jest {self.batch})")
        if self.workers is not None and self.workers < 0:
            errors.append(f"workers musi być >= 0 (jest {self.workers})")
        if self.lr0 <= 0:
            errors.append(f"lr0 musi być > 0 (jest {self.lr0})")
        if self.patience < 0:
            errors.append(f"patience musi być >= 0 (jest {self.patience})")
        if self.close_mosaic < 0:
            errors.append(f"close_mosaic musi być >= 0 (jest {self.close_mosaic})")
        if self.export_format and self.export_format not in SUPPORTED_EXPORTS:
            errors.append(
                f"Nieobsługiwany format eksportu '{self.export_format}' "
                f"(dozwolone: {', '.join(SUPPORTED_EXPORTS)})"
            )
        if self.resume and not Path(self.base_model).is_file():
            errors.append("--resume wymaga --base-model wskazującego plik checkpointu (np. .../weights/last.pt)")

        if errors:
            raise ConfigError("; ".join(errors))


@dataclass(frozen=True, slots=True)
class Accelerator:
    backend: str
    device: str
    description: str


def _is_rocm_build() -> bool:
    return bool(getattr(torch.version, "hip", None))


def _mps_available() -> bool:
    mps = getattr(torch.backends, "mps", None)
    return bool(mps and mps.is_available())


def _run_cmd(cmd: list[str]) -> str | None:
    if shutil.which(cmd[0]) is None:
        return None
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def hardware_info() -> dict[str, str]:
    info = {
        "torch": torch.__version__,
        "cuda_build": torch.version.cuda or "—",
        "hip_build": getattr(torch.version, "hip", None) or "—",
    }

    if torch.cuda.is_available():
        vendor = "amd" if _is_rocm_build() else "nvidia"
        try:
            info[f"{vendor}_gpu"] = torch.cuda.get_device_name(0)
        except RuntimeError:
            info[f"{vendor}_gpu"] = "?"
        info[f"{vendor}_count"] = str(torch.cuda.device_count())
        if vendor == "nvidia":
            driver = _run_cmd(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
            if driver:
                info["nvidia_driver"] = driver.splitlines()[0]

    if _mps_available():
        info["apple_mps"] = "available"
    return info


def discover_accelerators() -> dict[str, Accelerator]:
    found: dict[str, Accelerator] = {}

    if torch.cuda.is_available():
        count = torch.cuda.device_count()
        if _is_rocm_build():
            found["rocm"] = Accelerator("rocm", "0", f"ROCm (AMD) — HIP {torch.version.hip}, urządzeń: {count}")
        else:
            found["cuda"] = Accelerator("cuda", "0", f"CUDA (NVIDIA) — {torch.version.cuda}, urządzeń: {count}")

    if _mps_available():
        found["mps"] = Accelerator("mps", "mps", "MPS (Apple Silicon)")

    found["cpu"] = Accelerator("cpu", "cpu", "CPU")
    return found


def _select_gpu_ids(ids: str, available: dict[str, Accelerator]) -> Accelerator:
    gpu = next((available[name] for name in GPU_BACKENDS if name in available), None)
    if gpu is None:
        raise ConfigError(f"Podano ID GPU '{ids}', ale nie wykryto CUDA ani ROCm.")

    count = torch.cuda.device_count()
    invalid = [i for i in ids.split(",") if int(i) >= count]
    if invalid:
        raise ConfigError(f"Nieprawidłowe ID GPU: {', '.join(invalid)} (dostępne: 0–{count - 1}).")
    return Accelerator(gpu.backend, ids, f"{gpu.description}, wybrane: {ids}")


def resolve_accelerator(requested: str) -> Accelerator:
    request = requested.strip().lower()
    available = discover_accelerators()

    if request == "auto":
        return next(iter(available.values()))
    if GPU_IDS_PATTERN.fullmatch(request):
        return _select_gpu_ids(request, available)
    if request not in BACKENDS:
        raise ConfigError(
            f"Nieznane urządzenie '{requested}'. Dozwolone: {', '.join(BACKENDS)} "
            "lub ID GPU (np. '0', '0,1')."
        )
    if request not in available:
        raise ConfigError(
            f"Żądano backendu '{request}', ale nie jest dostępny "
            f"(dostępne: {', '.join(available)}). Użyj --device auto, aby wybrać automatycznie."
        )
    return available[request]


def running_in_container() -> bool:
    return (
        Path("/.dockerenv").exists()
        or bool(os.environ.get("DOCKER_CONTAINER"))
        or bool(os.environ.get("WSL_DISTRO_NAME"))
    )


def resolve_workers(requested: int | None) -> int:
    if requested is not None:
        return requested
    if running_in_container():
        LOG.info("Wykryto kontener/WSL — domyślnie workers=0 (unikanie problemów z shared memory).")
        return 0
    return DEFAULT_WORKERS


def _normalize_names(names: Any) -> list[str]:
    if isinstance(names, dict):
        return [str(value) for value in names.values()]
    if isinstance(names, (list, tuple)):
        return [str(value) for value in names]
    return []


def _split_entries(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def sanity_check_dataset(yaml_path: Path) -> None:
    try:
        with yaml_path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Niepoprawny plik YAML {yaml_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Niepoprawna struktura pliku YAML: {yaml_path}")

    names = _normalize_names(data.get("names"))
    if not names:
        raise ConfigError(f"Brak sekcji 'names' w pliku {yaml_path}")

    root = Path(data.get("path", ".")).expanduser()
    if not root.is_absolute():
        root = (yaml_path.parent / root).resolve()

    for split in ("train", "val"):
        raw = data.get(split) or (data.get("validation") if split == "val" else None)
        entries = _split_entries(raw)
        if not entries:
            raise ConfigError(f"Brak sekcji '{split}' w pliku {yaml_path}")
        for entry in entries:
            resolved = (root / entry).resolve()
            if not resolved.exists():
                raise ConfigError(f"Katalog splitu '{split}' nie istnieje: {resolved}")
            LOG.info("Split %-5s → %s", split, resolved)

    LOG.info("Wykryto klasy (%d): %s", len(names), ", ".join(names))


def make_run_name(base: str) -> str:
    return f"{base}_{datetime.now():%Y%m%d_%H%M%S}"


def build_train_kwargs(cfg: TrainingConfig, device: str, workers: int) -> dict[str, Any]:
    if cfg.resume:
        return {"resume": True, "device": device}

    return {
        "data": str(cfg.dataset_yaml),
        "epochs": cfg.epochs,
        "imgsz": cfg.imgsz,
        "batch": cfg.batch,
        "project": str(cfg.project),
        "name": cfg.run_name,
        "exist_ok": False,
        "save": True,
        "plots": True,
        "val": True,
        "device": device,
        "workers": workers,
        "optimizer": cfg.optimizer,
        "lr0": cfg.lr0,
        "patience": cfg.patience,
        "close_mosaic": cfg.close_mosaic,
        "cache": cfg.cache,
        "seed": cfg.seed,
        "verbose": True,
    }


def log_environment() -> None:
    LOG.info("=== Informacje o środowisku ===")
    for key, value in hardware_info().items():
        LOG.info("  %-15s %s", f"{key}:", value)


def train(cfg: TrainingConfig) -> YOLO:
    cfg.validate()
    sanity_check_dataset(cfg.dataset_yaml)
    log_environment()

    accelerator = resolve_accelerator(cfg.device)
    workers = resolve_workers(cfg.workers)
    LOG.info("Sprzęt: %s → device=%s", accelerator.description, accelerator.device)
    LOG.info("Model bazowy: %s", cfg.base_model)

    if cfg.resume:
        LOG.info("Wznawianie treningu z pliku checkpointu...")
    else:
        LOG.info("Rozpoczęcie treningu → %s", cfg.run_dir)
        LOG.info(
            "  epochs=%d imgsz=%d batch=%d workers=%d",
            cfg.epochs, cfg.imgsz, cfg.batch, workers,
        )

    model = YOLO(cfg.base_model)
    model.train(**build_train_kwargs(cfg, accelerator.device, workers))

    save_dir = getattr(getattr(model, "trainer", None), "save_dir", None)
    LOG.info("Trening zakończony pomyślnie.%s", f" Wyniki zapisane w: {save_dir}" if save_dir else "")
    return model


def export_model(model: YOLO, fmt: str) -> Path | None:
    LOG.info("Rozpoczynanie eksportu modelu do formatu: %s...", fmt)
    try:
        output = model.export(format=fmt)
    except Exception:
        LOG.exception("Eksport do formatu '%s' nie powiódł się.", fmt)
        return None
    path = Path(output) if output else None
    LOG.info("Model pomyślnie wyeksportowany: %s", path)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Trenuj dedykowany model YOLO do detekcji błędów i elementów UI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_YAML, help="Ścieżka do dataset YAML.")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL, help="Nazwa pliku modelu (np. yolov8n.pt) lub ścieżka do checkpointu.")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT, help="Katalog projektowy dla wyników treningu.")
    parser.add_argument("--name", default=DEFAULT_RUN_NAME, help="Bazowa nazwa uruchomienia (dopisywany jest timestamp).")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640, help=f"Rozmiar obrazu wejściowego (wielokrotność {MIN_IMGSZ}).")
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument(
        "--device", default="auto",
        help=f"{' | '.join(BACKENDS)} | ID GPU ('0', '0,1').",
    )
    parser.add_argument(
        "--workers", type=int, default=None,
        help=f"Liczba workerów DataLoadera (domyślnie: {DEFAULT_WORKERS}, w kontenerze/WSL: 0).",
    )
    parser.add_argument("--optimizer", default="AdamW", help="Optymalizator: 'AdamW', 'SGD', 'auto'...")
    parser.add_argument("--lr0", type=float, default=1e-3, help="Początkowy współczynnik uczenia.")
    parser.add_argument("--patience", type=int, default=30, help="Early stopping (0 = wyłączony).")
    parser.add_argument("--close-mosaic", type=int, default=10, help="Liczba ostatnich epok bez augmentacji mozaikowej.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cache", action="store_true", help="Buforuj obrazy w pamięci RAM.")
    parser.add_argument("--resume", action="store_true", help="Wznów trening z pliku checkpointu (wymaga --base-model).")
    parser.add_argument("--export", dest="export_format", choices=SUPPORTED_EXPORTS, default=None, help="Format eksportu po zakończonym treningu.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Włącz szczegółowe logi wyjściowe.")
    return parser


def parse_args(argv: Sequence[str] | None = None) -> tuple[TrainingConfig, bool]:
    args = build_parser().parse_args(argv)

    # Gdy wznawiamy trening, używamy zadanego name bez doklejania nowego timestampu
    run_name = args.name if args.resume else make_run_name(args.name)

    cfg = TrainingConfig(
        dataset_yaml=args.dataset.resolve(),
        base_model=args.base_model,
        project=args.project.resolve(),
        run_name=run_name,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        optimizer=args.optimizer,
        lr0=args.lr0,
        patience=args.patience,
        close_mosaic=args.close_mosaic,
        seed=args.seed,
        cache=args.cache,
        resume=args.resume,
        export_format=args.export_format,
    )
    return cfg, args.verbose


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: Sequence[str] | None = None) -> int:
    cfg, verbose = parse_args(argv)
    setup_logging(verbose=verbose)

    try:
        model = train(cfg)
    except KeyboardInterrupt:
        LOG.warning("Trening został przerwany przez użytkownika.")
        return EXIT_INTERRUPTED
    except ConfigError as exc:
        LOG.error("%s", exc)
        return EXIT_USAGE
    except Exception:
        LOG.exception("Trening zakończył się nieoczekiwanym błędem.")
        return EXIT_ERROR

    if cfg.export_format and export_model(model, cfg.export_format) is None:
        return EXIT_EXPORT_FAILED

    LOG.info("Zakończono pomyślnie.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
