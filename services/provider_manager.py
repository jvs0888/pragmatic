import asyncio
import re
import typing as t
from pathlib import Path

from playwright.async_api import Page, Frame

try:
    from loggers.logger import logger
except ImportError as ie:
    exit(f"{ie} :: {Path(__file__).resolve()}")


class ProviderManager:
    def __init__(self) -> None:
        self.handlers: dict = {
            "Penguin King":  self._process_penguin,
            "Hacksaw Gaming": self._process_hacksaw,
            "Playson": self._process_playson,
            "1x2gaming": self._process_1x2gaming,
            "Jacks": self._process_jacks,
            "Spinomenal": self._process_spinomenal,
            "Iron Dog": self._process_irondog,
            "Game Time Tec": self._process_gametimetec,
            # "Novomatic": self._process_novomatic
        }
        self.rtp_data: t.Optional[dict] = None
        self._data_received: asyncio.Event = asyncio.Event()
        self._timeout: int = 30

    async def process_game(self, provider_name: str, page: Page, game_name: str) -> t.Optional[dict]:
        handler: t.Optional = self.handlers.get(provider_name)

        if not handler:
            logger.warning(f"Unknown provider: {provider_name}")
            return None

        self._data_received.clear()
        self.rtp_data = None

        logger.info(f"Processing game: {game_name} | Provider: {provider_name}")

        result: t.Optional[dict] = await handler(page, game_name)
        return result

    async def _wait_for_data(self, game_name: str) -> t.Optional[dict]:
        try:
            await asyncio.wait_for(self._data_received.wait(), timeout=self._timeout)
            logger.info(f"RTP data received for game: {game_name} | RTP: {self.rtp_data.get('rtp')}")
            return self.rtp_data
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for RTP data: {game_name}")
            return None

    async def _process_penguin(self, page: Page, game_name: str) -> t.Optional[dict]:
        async def response_handler(response):
            if "/init" in response.url:
                try:
                    data: dict = await response.json()
                    rtp = data.get("result", {}).get("game", {}).get("rtp", {}).get("game")
                    if rtp:
                        self.rtp_data = {
                            "game": game_name,
                            "rtp": rtp
                        }
                        self._data_received.set()
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        page.on("response", response_handler)
        return await self._wait_for_data(game_name)

    async def _process_hacksaw(self, page: Page, game_name: str) -> t.Optional[dict]:
        async def response_handler(response):
            if "/api/meta/gameInfo" in response.url:
                try:
                    data: dict = await response.json()
                    rtp = data.get("data", {}).get("rtp")
                    if rtp:
                        self.rtp_data = {
                            "game": game_name,
                            "rtp": rtp
                        }
                        self._data_received.set()
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        page.on("response", response_handler)
        return await self._wait_for_data(game_name)

    async def _process_playson(self, page: Page, game_name: str) -> t.Optional[dict]:
        async def response_handler(response):
            if "/reconnect" in response.url:
                try:
                    text: str = await response.text()
                    if "<rtp>" in text:
                        match = re.search(r'<rtp>([\d.]+)</rtp>', text)
                        if match:
                            self.rtp_data = {
                                "game": game_name,
                                "rtp": float(match.group(1))
                            }
                            self._data_received.set()
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        page.on("response", response_handler)
        return await self._wait_for_data(game_name)

    async def _process_jacks(self, page: Page, game_name: str) -> t.Optional[dict]:
        async def response_handler(response):
            if "/sj/common" in response.url:
                try:
                    data: dict = await response.json()
                    rtp = data.get("rtp", {}).get("base")
                    if rtp:
                        self.rtp_data = {
                            "game": game_name,
                            "rtp": rtp
                        }
                        self._data_received.set()
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        page.on("response", response_handler)
        return await self._wait_for_data(game_name)

    async def _process_spinomenal(self, page: Page, game_name: str) -> t.Optional[dict]:
        async def response_handler(response):
            if "/scripts/inter_service" in response.url:
                try:
                    text: str = await response.text()
                    if "'RTP'" in text:
                        match = re.search(
                            r"'Result'\s*:\s*\{[^}]*'MathProfile'\s*:\s*\{[^}]*'RTP'\s*:\s*([\d.]+)",
                            text,
                            re.DOTALL
                        )
                        if match:
                            self.rtp_data = {
                                "game": game_name,
                                "rtp": float(match.group(1))
                            }
                            self._data_received.set()
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        page.on("response", response_handler)
        return await self._wait_for_data(game_name)

    async def _process_gametimetec(self, page: Page, game_name: str) -> t.Optional[dict]:
        async def response_handler(response):
            if "/localization/en" in response.url:
                try:
                    data: dict = await response.json()
                    text: str = data.get("RETURN_TO_PLAYER_PARA", {})
                    if text:
                        match = re.search(r'theoretical RTP of .+ is ([\d.]+)%', text)
                        if match:
                            self.rtp_data = {
                                "game": game_name,
                                "rtp": float(match.group(1))
                            }
                            self._data_received.set()
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        page.on("response", response_handler)
        return await self._wait_for_data(game_name)

    async def _process_1x2gaming(self, page: Page, game_name: str) -> t.Optional[dict]:
        try:
            frame: t.Optional[Frame] = None
            for _ in range(20):
                frame = next((f for f in page.frames if "desertorchidhub" in f.url), None)
                if frame:
                    break
                await asyncio.sleep(1)

            if not frame:
                logger.error("1x2gaming iframe not found")
                return None

            await frame.wait_for_selector('button.ui-preloader-sound-on', timeout=30000)
            await frame.click('button.ui-preloader-sound-on')

            try:
                await frame.wait_for_selector('button.help-screen_btn', timeout=5000)
                await frame.click('button.help-screen_btn')
            except Exception:
                pass

            await frame.wait_for_selector('button.ui-menu-button', timeout=15000)
            await frame.click('button.ui-menu-button')
            await frame.click('button.ui-menu-game-guide-button')

            await frame.wait_for_selector('[ng-reflect-vals]', timeout=5000)
            rtp_raw: str = await frame.get_attribute('[ng-reflect-vals]', 'ng-reflect-vals')

            if rtp_raw:
                rtp: str = rtp_raw.replace('%', '').strip()
                self.rtp_data = {"game": game_name, "rtp": float(rtp)}
                self._data_received.set()

        except Exception as e:
            logger.error(f"Error processing 1x2gaming: {e}")

        return await self._wait_for_data(game_name)

    async def _process_irondog(self, page: Page, game_name: str) -> t.Optional[dict]:
        if game_name == '3 Runaway Riches':
            try:
                frame: t.Optional[Frame] = None
                for _ in range(20):
                    frame = next((f for f in page.frames if "gamelauncher.desertorchidhub" in f.url), None)
                    if frame:
                        break
                    await asyncio.sleep(1)

                if not frame:
                    logger.error("iframe not found")
                    return None

                await asyncio.sleep(15)
                await page.mouse.click(748, 865)
                await asyncio.sleep(3)

                game_frame: t.Optional[Frame] = None
                for _ in range(20):
                    all_frames: list = [f.url for f in page.frames]
                    logger.info(f"frames: {all_frames}")
                    game_frame = next((f for f in page.frames if "cdn.desertorchidhub" in f.url), None)
                    if game_frame:
                        break
                    await asyncio.sleep(1)

                if not game_frame:
                    logger.error("iframe not found")
                    return None

                await game_frame.click('button svg[role="img"]')

                await game_frame.wait_for_selector('text=RTP', timeout=10000)
                text = await game_frame.inner_text('body')
                match = re.search(r'RTP of ([\d.]+)%', text)
                if match:
                    self.rtp_data = {"game": game_name, "rtp": float(match.group(1))}
                    self._data_received.set()
                    logger.info(f"RTP found: {match.group(1)}")

            except Exception as e:
                logger.error(f"Error processing irondog: {e}")

            return await self._wait_for_data(game_name)
        else:
            return await self._process_1x2gaming(page, game_name)
