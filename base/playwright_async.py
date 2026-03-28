import asyncio
import os
import random
import typing as t
from pathlib import Path

from playwright.async_api import (
    async_playwright, Playwright, Browser, BrowserContext, Page, ElementHandle, TimeoutError
)

try:
    from loggers.logger import logger
except ImportError as ie:
    exit(f"{ie} :: {Path(__file__).resolve()}")


class PlaywrightAsync:
    def __init__(self):
        self.project_path: Path = Path(__file__).resolve().parent.parent
        self.videos_path: str = os.path.join(self.project_path, "sources", "videos")
        self.user_data_dir: str = "/tmp/chrome-profile"
        self.host: str = "http://127.0.0.1"
        self.port: int = 9222
        self.browser_process: t.Optional[asyncio.subprocess.Process] = None
        self.playwright: t.Optional[Playwright] = None
        self.browser: t.Optional[Browser] = None
        self.context: t.Optional[BrowserContext] = None
        self.page: t.Optional[Page] = None

    @staticmethod
    async def human_type(element: ElementHandle, text: str) -> None:
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.2))

    async def close(self) -> None:
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.browser_process:
            if self.browser_process.returncode is None:
                self.browser_process.terminate()
                await self.browser_process.wait()
            if self.browser_process.returncode is None:
                self.browser_process.kill()
                await self.browser_process.wait()

    async def wait_for_selector(self, selector: str, timeout: int = 15000) -> ElementHandle:
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

            self.playwright: Playwright = await async_playwright().start()
            self.browser: Browser = await self.playwright.chromium.launch(channel="chrome", headless=headless)
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

    async def init_browser_process(self) -> bool:
        if not os.path.exists(path=self.user_data_dir):
            os.makedirs(name=self.user_data_dir, exist_ok=True)

        command: str = (
            'google-chrome '
            f'--user-data-dir={self.user_data_dir} '
            f'--remote-debugging-port={self.port} '
            '--window-size=1920,1080 '
            '--start-maximized '
        )

        logger.info(f'open browser using :: {command}')
        self.browser_process: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        return True

    async def connect_cdp_session(self, playwright: Playwright) -> bool:
        endpoint_url: str = f'{self.host}:{self.port}'

        try:
            self.browser = await playwright.chromium.connect_over_cdp(endpoint_url=endpoint_url)
            # self.context = self.browser.contexts
            self.context: BrowserContext = self.browser.contexts[0]
            self.page: Page = self.context.pages[0]
        except Exception:
            logger.error(f'connection error :: {endpoint_url}')
            return False

        logger.info(f'connection established to existed browser session :: {endpoint_url}')
        return True
