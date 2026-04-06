import asyncio
from playwright.async_api import Page
from utils.logger import get_logger
import config

log = get_logger("Actions")


async def place_bet(page: Page, team_row) -> None:
    log.info("Clicking back odd to open bet panel...")
    await team_row.locator(".back.lock").click()

    bet_panel = page.locator("table.coupon-table", has_text="Bet for")
    await bet_panel.wait_for(state="visible", timeout=10_000)
    log.info("Bet panel opened.")

    stake_input = bet_panel.locator("td.bet-stakes input")
    await stake_input.wait_for(state="visible", timeout=5_000)
    await stake_input.click()
    await stake_input.fill(str(config.BET_STAKE))
    await stake_input.dispatch_event("input")
    await stake_input.dispatch_event("change")
    log.info(f"Stake entered: {config.BET_STAKE}")

    submit_button = page.locator("button.btn-success", has_text="Submit")
    await submit_button.wait_for(state="visible", timeout=5_000)
    for _ in range(20):
        if await submit_button.is_enabled():
            break
        await asyncio.sleep(0.5)

    await submit_button.click()
    log.info("Bet submitted.")

    await bet_panel.wait_for(state="hidden", timeout=10_000)
    log.info("Bet panel closed.")