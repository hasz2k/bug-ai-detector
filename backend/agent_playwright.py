from __future__ import annotations

import argparse
import asyncio
import logging
import random
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, async_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
VIDEOS_DIR = BASE_DIR / "videos"

DEFAULT_URL = "http://localhost:8085"
VIEWPORT = {"width": 1280, "height": 720}
STEP_PAUSE_S = 1
CLICK_TIMEOUT_MS = 2000


@dataclass(frozen=True)
class Step:
    action: str
    value: int | str


TEST_STEPS = [
    Step("scroll", 400),
    Step("wait", 1500),
    Step("scroll", 800),
    Step("click_random", "button, a"),
    Step("wait", 2000),
]


async def scroll(page: Page, y: int) -> str:
    await page.evaluate("y => window.scrollTo(0, y)", y)
    return f"Przewinięto widok do Y: {y}"


async def wait(page: Page, ms: int) -> str:
    await page.wait_for_timeout(ms)
    return f"Oczekiwanie {ms} ms"


async def click_random(page: Page, selector: str) -> str:
    elements = page.locator(selector)
    count = await elements.count()
    if count == 0:
        raise LookupError(f"Brak elementów pasujących do selektora: {selector!r}")
    await elements.nth(random.randrange(count)).click(timeout=CLICK_TIMEOUT_MS)
    return "Wykonano kliknięcie w losowy element interfejsu."


ACTIONS: dict[str, Callable[[Page, int | str], Awaitable[str]]] = {
    "scroll": scroll,
    "wait": wait,
    "click_random": click_random,
}


def setup_logger(timestamp: str) -> tuple[logging.Logger, Path]:
    log_path = LOGS_DIR / f"qa_session_{timestamp}.log"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    logger = logging.getLogger(f"QA_Agent_{timestamp}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    return logger, log_path


async def run_steps(page: Page, steps: list[Step], logger: logging.Logger) -> None:
    for idx, step in enumerate(steps, start=1):
        handler = ACTIONS.get(step.action)
        if handler is None:
            logger.warning("Krok %d: Nieznana akcja %r – pominięto.", idx, step.action)
            continue
        try:
            message = await handler(page, step.value)
            logger.info("Krok %d: %s", idx, message)
        except (PlaywrightError, LookupError) as exc:
            logger.warning("Krok %d: Akcja %r nie powiodła się: %s", idx, step.action, exc)
        await asyncio.sleep(STEP_PAUSE_S)


async def save_video(page: Page, target: Path, logger: logging.Logger) -> None:
    if page.video is None:
        return
    source = Path(await page.video.path())
    if source.exists():
        shutil.move(str(source), str(target))
        logger.info("Zapisano nagranie wideo sesji: %s", target)


async def run_autonomous_qa_agent(target_url: str = DEFAULT_URL, headless: bool = True) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger, log_path = setup_logger(timestamp)
    video_path = VIDEOS_DIR / f"qa_session_{timestamp}.webm"

    logger.info("Rozpoczęto autonomiczną sesję testową QA dla URL: %s", target_url)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            try:
                context = await browser.new_context(
                    viewport=VIEWPORT,
                    record_video_dir=str(VIDEOS_DIR),
                    record_video_size=VIEWPORT,
                )
                page = await context.new_page()
                try:
                    logger.info("Ładowanie strony docelowej...")
                    await page.goto(target_url, wait_until="networkidle")
                    logger.info("Strona załadowana pomyślnie.")

                    await run_steps(page, TEST_STEPS, logger)
                    logger.info("Sesja testowa zakończona.")
                except Exception:
                    logger.exception("Błąd podczas wykonywania testu Playwright")
                finally:
                    await context.close()
                    await save_video(page, video_path, logger)
            finally:
                await browser.close()
    finally:
        logger.info("Zapisano dziennik logów: %s", log_path)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autonomiczny agent QA (Playwright)")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="Adres testowanej strony")
    parser.add_argument("--headed", action="store_true", help="Uruchom z widoczną przeglądarką")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_autonomous_qa_agent(args.url, headless=not args.headed))
