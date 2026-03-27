# monitor.py — Odds monitor for one site

import asyncio
from playwright.async_api import Page
import config
from utils.logger import get_logger

async def monitor_site(page: Page) -> None:
    log = get_logger("Monitor")
    log.info(f"Monitor started. Will check odds every {config.POLL_INTERVAL_SECONDS} second(s).")

    # We'll add real odds-reading logic here later
    for i in range(3):
        log.info(f"Checking odds... (check #{i + 1})")
        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)

    log.info("Monitor finished.")