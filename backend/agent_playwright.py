import asyncio
import os
from playwright.async_api import async_playwright

async def run_autonomous_qa_agent(target_url: str = "http://localhost:8085"):
    """
    Autonomiczny agent QA przechodzący przez widoki aplikacji i rejestrujący błędy.
    """
    async with async_playwright() as p:
        # Uruchomienie przeglądarki Chromium
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        print(f"🤖 [Playwright Agent] Uruchamianie eksploracji dla: {target_url}")

        try:
            await page.goto(target_url, wait_until="networkidle")
            print("🤖 [Playwright Agent] Strona załadowana pomyślnie.")

            # Symulacja pętli eksploracyjnej agenta AI
            steps = [
                {"action": "scroll", "y": 400},
                {"action": "wait", "ms": 1500},
                {"action": "scroll", "y": 800},
                {"action": "click_random", "selector": "button, a"},
                {"action": "wait", "ms": 2000},
            ]

            for step in steps:
                if step["action"] == "scroll":
                    await page.evaluate(f"window.scrollTo(0, {step['y']})")
                    print(f"🤖 [Agent] Przewinięto do Y: {step['y']}")
                elif step["action"] == "wait":
                    await asyncio.sleep(step["ms"] / 1000)
                elif step["action"] == "click_random":
                    buttons = await page.query_selector_all(step["selector"])
                    if buttons:
                        # Kliknięcie pierwszego widocznego przycisku/linku
                        try:
                            await buttons[0].click(timeout=2000)
                            print("🤖 [Agent] Wykonano autonomiczne kliknięcie w interfejsie.")
                        except Exception as e:
                            print(f"⚠️ [Agent] Pominięto interakcję z elementem: {e}")

                await asyncio.sleep(1)

        except Exception as err:
            print(f"❌ [Playwright Agent Error]: {err}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_autonomous_qa_agent())
