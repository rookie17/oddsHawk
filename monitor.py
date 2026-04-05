# monitor.py — Odds monitor for one site

import asyncio
from playwright.async_api import Page
import config
from utils.logger import get_logger

async def monitor_site(page: Page) -> None:
    log = get_logger("Monitor")

    await _login_demo(page, log)

    # We'll add odds reading here in the next milestone
    log.info("Logged in. Monitoring will go here next.")

async def _login_demo(page: Page, log) -> None:
    log.info("Clicking 'Login with Demo ID'...")

    # Playwright concept: `get_by_text()`
    # Finds a button by its visible text. More readable than CSS selectors
    # and resilient to class name changes.
    await page.get_by_text("Login with Demo ID").click()

    # Wait until the page finishes navigating after login.
    # "networkidle" = no network requests for 500ms — means the page settled.
    await page.wait_for_load_state("networkidle")

    log.info("Login successful. Current URL: " + page.url)