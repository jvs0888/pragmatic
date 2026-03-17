import asyncio
import random
import typing as t
from pathlib import Path

from playwright.async_api import Frame

try:
    from loggers.logger import logger
    from base.playwright_async import PlaywrightAsync
    from services.spin_manager import SpinCollector
except ImportError as ie:
    exit(f"{ie} :: {Path(__file__).resolve()}")


class Pragmatic(PlaywrightAsync):
    def __init__(self):
        super().__init__()
        self.collector = SpinCollector()
        self.game_url: str = "https://www.pragmaticplay.com/en/games/gates-of-olympus"
        self.game_frame: t.Optional[Frame] = None

    async def close_alerts(self):
        tasks: list = [
            self.wait_for_selector(selector="//button[@data-cky-tag='reject-button']"),
            self.wait_for_selector(selector="//a[@data-age-check-confirm]")
        ]

        for coro in asyncio.as_completed(tasks):
            element = await coro
            if not element:
                continue

            await element.click()

    async def load_frame(self):
        self.game_frame: Frame = next(f for f in self.page.frames if "html5Game.do" in f.url)
        await self.game_frame.wait_for_selector("//div[@id='ScaleRootLoading']", state="hidden")

    async def set_autoplay(self):
        autoplay_clicks = {
            "focus_frame": (500, 300),
            "enter_game": (1130, 445),
            "autoplay_option": (1050, 640),
            "autoplay_start": (800, 490),
        }

        for coords in autoplay_clicks.values():
            await self.page.mouse.click(*coords)
            random_sleep: int = random.randint(2, 4)
            await asyncio.sleep(random_sleep)

    async def execute(self):
        try:
            if not await self.init_browser():
                logger.error("Browser not initialized")
                return

            await self.intercept_responses(url_pattern="/gameService", callback=self.collector.process_response)

            await self.page.goto(url=self.game_url)
            await self.close_alerts()
            await self.load_frame()
            await self.set_autoplay()

            await self.collector.wait_until_done()
            self.collector.save_xlsx()
        except Exception as e:
            logger.error(e)
        finally:
            await self.close()

    def run(self):
        try:
            asyncio.run(self.execute())
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise
        except Exception:
            pass
