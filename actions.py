import asyncio
from playwright.async_api import Page
from utils.logger import get_logger
import config

log = get_logger("Actions")


async def place_bet(page: Page, team_row, bet_stake: float) -> None:
    log.info("Clicking back odd to open bet panel...")
    await team_row.locator(".back.lock").click()

    bet_panel = page.locator("table.coupon-table", has_text="Bet for")
    await bet_panel.wait_for(state="visible", timeout=10_000)
    log.info("Bet panel opened.")

    stake_input = bet_panel.locator("td.bet-stakes input")
    await stake_input.wait_for(state="visible", timeout=5_000)
    await stake_input.click()
    await stake_input.fill(str(bet_stake))
    await stake_input.dispatch_event("input")
    await stake_input.dispatch_event("change")
    log.info(f"Stake entered: {bet_stake}")

    submit_button = page.locator("button.btn-success", has_text="Submit")
    await submit_button.wait_for(state="visible", timeout=5_000)
    for _ in range(20):
        if await submit_button.is_enabled():
            break
        await asyncio.sleep(0.5)

    await submit_button.click()
    log.info("Submit clicked. Waiting for outcome...")

    await _check_bet_outcome(page)

async def _check_bet_outcome(page: Page) -> None:
    success_toast = page.locator(".toast-success")
    error_toast = page.locator(".toast-error")

    for _ in range(20):
        await asyncio.sleep(0.25)

        if await success_toast.count() > 0:
            try:
                message = (await success_toast.locator(".toast-message").inner_text(timeout=1_000)).strip()
            except Exception:
                message = "Bet placed"
            log.info(f"Bet confirmed: '{message}'")
            return

        if await error_toast.count() > 0:
            try:
                message = (await error_toast.locator(".toast-message").inner_text(timeout=1_000)).strip()
            except Exception:
                message = "Unknown error"
            log.error(f"Bet rejected: '{message}'")
            raise RuntimeError(f"Bet rejected: {message}")

    raise RuntimeError("Bet outcome timeout — no toast appeared within 5 seconds.")