# main.py — Entry point for OddsHawk

import asyncio
from playwright.async_api import async_playwright
import config
from utils.logger import get_logger
from monitor import monitor_site

log = get_logger("OddsHawk")

async def run():
    log.info("OddsHawk starting up...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        log.info("Browser launched.")

        page = await browser.new_page()
        await page.goto(config.SITE_URL)
        log.info(f"Opened: {config.SITE_URL}")

        await monitor_site(page)

        await browser.close()
        log.info("Browser closed. Done.")

asyncio.run(run())