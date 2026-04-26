import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from utils.logger import get_logger
from actions import submit_cashout_panel, _check_bet_outcome

log = get_logger("Test.CashoutOutcome")

MOCK_URL = (Path(__file__).parent / "mock_cashout.html").resolve().as_uri()

# Change this to test different outcomes:
# "success" | "error" | "silent"
SIMULATE = "success"

CASHOUT_TARGET = 40.0


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        log.info(f"Loading mock page: {MOCK_URL}")
        await page.goto(MOCK_URL)

        # Set the outcome radio before doing anything
        await page.locator(f'input[name="outcome"][value="{SIMULATE}"]').check()
        log.info(f"Outcome set to: '{SIMULATE}'")

        # --- Read cashout amount before opening panel ---
        amount_span = page.locator("#cashout-amount")

        # --- Click cashout to open panel (mirrors open_cashout_panel) ---
        log.info("Clicking cashout button...")
        await page.locator("button.btn_cashout").click()
        bet_panel = page.locator("table.coupon-table", has_text="Bet for")
        await bet_panel.wait_for(state="visible", timeout=5_000)
        log.info("Panel open.")

        # --- Read amount (mirrors _read_cashout_amount) ---
        amount_text = (await amount_span.inner_text()).strip()
        amount = float(amount_text)
        log.info(f"Cashout amount: {amount} | Target: {CASHOUT_TARGET}")

        if amount >= CASHOUT_TARGET:
            log.info("Target hit. Submitting...")
            try:
                await submit_cashout_panel(page)
                log.info("TEST PASSED — outcome detected correctly.")
            except RuntimeError as e:
                log.error(f"TEST FAILED — outcome detection raised: {e}")
        else:
            log.info(f"Amount {amount} below target {CASHOUT_TARGET} — no submit.")

        await asyncio.sleep(5)
        await browser.close()


asyncio.run(run())