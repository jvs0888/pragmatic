import asyncio
import os
import typing as t
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, ElementHandle, TimeoutError

try:
    from loggers.logger import logger
except ImportError as ie:
    exit(f"{ie} :: {Path(__file__).resolve()}")


class PlaywrightAsync:
    def __init__(self):
        self.project_path: Path = Path(__file__).resolve().parent.parent
        self.videos_path: str = os.path.join(self.project_path, "sources", "videos")
        self.playwright = None
        self.browser: t.Optional[Browser] = None
        self.context: t.Optional[BrowserContext] = None
        self.page: t.Optional[Page] = None

    async def close(self) -> None:
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def wait_for_selector(self, selector: str, timeout: int = 15000, save_screen: bool = False) -> ElementHandle:
        try:
            element: ElementHandle = await self.page.wait_for_selector(selector=selector, timeout=timeout)
            logger.info(f"selector found :: {selector}")
            return element
        except TimeoutError:
            logger.error(f"selector not found :: {selector}")

    async def init_browser(self, headless: bool = False, record_video: bool = True) -> bool:
        try:
            context_options = dict()
            if record_video:
                context_options["record_video_dir"] = self.videos_path

            self.playwright = await async_playwright().start()
            self.browser: Browser = await self.playwright.chromium.launch(headless=headless)
            self.context: BrowserContext = await self.browser.new_context(
                **context_options,
                viewport={"width": 1600, "height": 900}
            )
            self.page: Page = await self.context.new_page()
            return True
        except Exception as e:
            logger.error(f"connection error :: {e}")
            return False

    async def intercept_responses(self, url_pattern: str, callback: t.Callable) -> None:
        async def handler(response):
            if url_pattern in response.url:
                text = await response.text()
                if asyncio.iscoroutinefunction(callback):
                    await callback(text)
                else:
                    callback(text)

        self.page.on("response", handler)
