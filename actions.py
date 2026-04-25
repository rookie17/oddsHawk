import asyncio
from playwright.async_api import Page
from utils.logger import get_logger

log = get_logger("Actions")


async def place_bet(page: Page, team_row, bet_stake: float) -> None:
    # Extract team name from the row so we can verify against My Bet table later
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


async def _check_bet_outcome(page: Page, team_name: str) -> None:
    success_toast = page.locator(".toast-success")
    error_toast = page.locator(".toast-error")

    # my-bet table rows — tr.back means a placed bet entry exists
    # We check if any row's first td contains our team name
    my_bet_rows = page.locator("div.card.my-bet tr.back")

    for _ in range(20):
        await asyncio.sleep(0.25)

        # Fast path: toast appeared
        if await success_toast.count() > 0:
            try:
                message = (await success_toast.locator(".toast-message").inner_text(timeout=1_000)).strip()
            except Exception:
                message = "Bet placed"
            log.info(f"Bet confirmed via toast: '{message}'")
            return

        if await error_toast.count() > 0:
            try:
                message = (await error_toast.locator(".toast-message").inner_text(timeout=1_000)).strip()
            except Exception:
                message = "Unknown error"
            log.error(f"Bet rejected: '{message}'")
            raise RuntimeError(f"Bet rejected: {message}")

        # Fallback: check My Bet table for a row matching this team
        # inner_text() on each tr.back's first td to match team name
        row_count = await my_bet_rows.count()
        for i in range(row_count):
            row = my_bet_rows.nth(i)
            # First td in each tr.back holds the team name
            nation_td = row.locator("td").first
            try:
                nation_text = (await nation_td.inner_text(timeout=500)).strip()
            except Exception:
                continue
            if team_name.lower() in nation_text.lower():
                log.info(f"Bet confirmed via My Bet table: '{nation_text}' found.")
                return

    raise RuntimeError("Bet outcome timeout — no toast or My Bet entry appeared within 5 seconds.")