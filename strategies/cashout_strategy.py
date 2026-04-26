from playwright.async_api import Page
import asyncio
from utils.logger import get_logger
from actions import place_bet, perform_cashout
from monitor import navigate_to_any_match
from actions import place_bet, perform_cashout, open_cashout_panel, submit_cashout_panel

log = get_logger("Strategy.Cashout")


async def _get_team_row(page: Page, team_name: str):
    """
    Locates the .table-row whose team name contains team_name (case-insensitive).
    Raises if not found — the user should double-check the spelling.
    """
    match_odds_table = page.locator(".table-body", has=page.locator(".back.lock")).first
    rows = match_odds_table.locator(".table-row")
    count = await rows.count()
    for i in range(count):
        row = rows.nth(i)
        name = (await row.locator(".team-name b").first.inner_text()).strip()
        if team_name.lower() in name.lower():
            log.info(f"Team row located: '{name}'")
            return row
    raise RuntimeError(
        f"Team '{team_name}' not found on the match page. "
        "Check spelling or verify the correct match was opened."
    )


async def _wait_for_bet_live(page: Page, timeout: float = 5.0) -> None:
    """
    Waits until the My Bet panel appears with at least one bet row (tr.back).
    This confirms the placed bet is live and the cashout button should become enabled.
    Falls through after timeout — cashout monitor handles the disabled button gracefully.
    
    .card.my-bet — the active bets card that only renders when a bet is live.
    tr.back inside it — the individual bet row (back bet).
    """
    log.info("Waiting for My Bet panel to confirm bet is live...")
    my_bet_row = page.locator(".card.my-bet tr.back")
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if await my_bet_row.count() > 0:
            log.info("Bet confirmed live in My Bet panel.")
            return
        await asyncio.sleep(0.2)
    log.warning("My Bet panel not seen within 5s — continuing anyway.")


async def _read_cashout_amount(team_row) -> float | None:
    """
    Reads the live cashout amount from the team row.
    
    The span.float-right inside .country-name p is only injected into the DOM
    when a bet is active. Returns None if the span is absent (no active bet yet)
    or if parsing fails.
    
    Can return a negative float when cashout would result in a loss (span turns text-red).
    """
    try:
        span = team_row.locator(".country-name p span.float-right")
        if await span.count() == 0:
            return None
        text = (await span.inner_text()).strip()
        return float(text)
    except Exception:
        return None


async def _monitor_by_odds(page: Page, team_row, cashout_target: float) -> None:
    """
    Monitors the team's best back odd (.back.lock .odd).
    Triggers cashout when odd >= cashout_target.
    Polls every 1 second — odds change on every market tick, not faster.
    """
    odd_locator = team_row.locator(".back.lock .odd")
    log.info(f"Monitoring back odd. Cashout when odd >= {cashout_target}")

    while True:
        try:
            text = (await odd_locator.inner_text()).strip()
            if text == "-":
                log.info("Market suspended. Waiting...")
                await asyncio.sleep(1.0)
                continue
            current = float(text)
            log.info(f"Back odd: {current} | Target: {cashout_target}")
            if current >= cashout_target:
                log.info(f"Target hit — odd {current} >= {cashout_target}. Executing cashout.")
                await perform_cashout(page)
                return
        except Exception as e:
            log.warning(f"Error reading odd: {e}")
        await asyncio.sleep(1.0)


async def _monitor_by_amount(page: Page, team_row, cashout_target: float) -> None:
    log.info(f"Clicking cashout every 1s. Target amount: >= {cashout_target}")

    while True:
        log.info("Clicking cashout button...")
        panel_open = await open_cashout_panel(page)

        if not panel_open:
            log.warning("Cashout button not available. Retrying in 1s...")
            await asyncio.sleep(1.0)
            continue

        amount = await _read_cashout_amount(team_row)
        log.info(f"Cashout amount: {amount} | Target: {cashout_target}")

        if amount is not None and amount >= cashout_target:
            log.info(f"Target hit — {amount} >= {cashout_target}. Submitting.")
            await submit_cashout_panel(page)
            return

        try:
            close_btn = page.locator("button.btn-danger.float-left", has_text="Reset")
            await close_btn.click(timeout=2_000)
            log.info("Panel closed.")
        except Exception as e:
            log.warning(f"Could not close panel: {e}")

        await asyncio.sleep(1.0)


async def run(page: Page, params: dict) -> None:
    sub_mode = params["sub_mode"]
    team_name = params["team_name"]
    cashout_mode = params["cashout_mode"]
    cashout_target = params["cashout_target"]

    # Navigate to the correct match (strategy handles its own navigation)
    await navigate_to_any_match(page, team_name)
    team_row = await _get_team_row(page, team_name)

    if sub_mode == 1:
        # --- Option 1: Bet first, then cashout ---
        bet_stake = params["bet_stake"]
        bet_odds = params["bet_odds"]

        log.info(f"[Bet+Cashout] Waiting for back odd >= {bet_odds} on '{team_name}' to place bet...")
        odd_locator = team_row.locator(".back.lock .odd")
        bet_placed = False

        while not bet_placed:
            try:
                text = (await odd_locator.inner_text()).strip()
                if text == "-":
                    await asyncio.sleep(1.0)
                    continue
                current = float(text)
                log.info(f"Back odd: {current} | Bet trigger: {bet_odds}")
                if current >= bet_odds:
                    log.info(f"Bet trigger hit — {current} >= {bet_odds}. Placing bet...")
                    bet_placed = True  # lock before calling — same principle as BothTeamsSameOdd
                    try:
                        await place_bet(page, team_row, bet_stake)
                    except RuntimeError as e:
                        log.warning(f"Bet outcome uncertain: {e}. Treating as placed — moving to cashout.")
            except Exception as e:
                log.warning(f"Error reading odd: {e}")

            if not bet_placed:
                await asyncio.sleep(1.0)

        # Wait for My Bet panel to confirm bet is live before monitoring cashout
        await _wait_for_bet_live(page)

    else:
        # --- Option 2: Just cashout (bet already placed by user) ---
        log.info(f"[Just Cashout] Bet assumed live. Starting cashout monitor for '{team_name}'.")

    log.info(f"Cashout mode: {'back odd' if cashout_mode == 'odds' else 'cashout amount'} | Target: {cashout_target}")

    if cashout_mode == "odds":
        await _monitor_by_odds(page, team_row, cashout_target)
    else:
        await _monitor_by_amount(page, team_row, cashout_target)

    log.info("Cashout strategy complete.")