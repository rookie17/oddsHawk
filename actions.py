import asyncio
from playwright.async_api import Page
from utils.logger import get_logger

log = get_logger("Actions")


async def place_bet(page: Page, team_row, bet_stake: float) -> None:
    team_name = (await team_row.locator(".team-name b").first.inner_text()).strip()

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
    await _check_bet_outcome(page, team_name)


async def open_cashout_panel(page: Page) -> bool:
    cashout_button = page.locator("button.btn_cashout:not([disabled])")
    try:
        await cashout_button.wait_for(state="visible", timeout=5_000)
        await cashout_button.click()
        bet_panel = page.locator("table.coupon-table", has_text="Bet for")
        await bet_panel.wait_for(state="visible", timeout=5_000)
        log.info("Cashout panel opened.")
        return True
    except Exception as e:
        log.warning(f"Could not open cashout panel: {e}")
        return False


async def submit_cashout_panel(page: Page) -> None:
    submit_button = page.locator("button.btn-success", has_text="Submit")
    await submit_button.wait_for(state="visible", timeout=5_000)
    for _ in range(20):
        if await submit_button.is_enabled():
            break
        await asyncio.sleep(0.5)
    await submit_button.click()
    log.info("Cashout submit clicked. Waiting for outcome...")
    await _check_bet_outcome(page)


async def perform_cashout(page: Page) -> None:
    opened = await open_cashout_panel(page)
    if not opened:
        raise RuntimeError("Cashout panel did not open — button may be disabled.")
    await submit_cashout_panel(page)


async def _check_bet_outcome(page: Page, team_name: str = None) -> None:
    success_toast = page.locator(".toast-success")
    error_toast = page.locator(".toast-error")
    my_bet_rows = page.locator("div.card.my-bet tr.back")

    for _ in range(20):
        await asyncio.sleep(0.25)

        if await success_toast.is_visible():
            try:
                message = (await success_toast.locator(".toast-message").inner_text(timeout=1_000)).strip()
            except Exception:
                message = "Success"
            log.info(f"Confirmed: '{message}'")
            return

        if await error_toast.is_visible():
            try:
                message = (await error_toast.locator(".toast-message").inner_text(timeout=1_000)).strip()
            except Exception:
                message = "Unknown error"
            log.error(f"Rejected: '{message}'")
            raise RuntimeError(f"Rejected: {message}")

        if team_name:
            row_count = await my_bet_rows.count()
            for i in range(row_count):
                try:
                    nation_text = (await my_bet_rows.nth(i).locator("td").first.inner_text(timeout=500)).strip()
                    if team_name.lower() in nation_text.lower():
                        log.info(f"Confirmed via My Bet table: '{nation_text}'")
                        return
                except Exception:
                    continue

    raise RuntimeError("Outcome timeout — no toast or My Bet entry appeared within 5 seconds.")