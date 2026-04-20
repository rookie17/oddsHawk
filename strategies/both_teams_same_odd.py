from playwright.async_api import Page
import asyncio
from utils.logger import get_logger
from actions import place_bet

log = get_logger("Strategy.BothTeamsSameOdd")


async def run(page: Page, params: dict) -> None:
    target_odds = params["target_odds"]
    bet_stake = params["bet_stake"]

    log.info(f"Monitoring both teams. Target odd: {target_odds} | Stake: {bet_stake}")

    match_odds_table = page.locator(".table-body", has=page.locator(".back.lock")).first

    team1_row = match_odds_table.locator(".table-row").nth(0)
    team2_row = match_odds_table.locator(".table-row").nth(1)

    team1_name = (await team1_row.locator(".team-name b").first.inner_text()).strip()
    team2_name = (await team2_row.locator(".team-name b").first.inner_text()).strip()
    log.info(f"Monitoring: [{team1_name}] vs [{team2_name}]")

    team1_odd_locator = team1_row.locator(".back.lock .odd")
    team2_odd_locator = team2_row.locator(".back.lock .odd")

    team1_bet_placed = False
    team2_bet_placed = False

    while True:
        try:
            team1_text = (await team1_odd_locator.inner_text()).strip()
            team2_text = (await team2_odd_locator.inner_text()).strip()

            if team1_text == "-" or team2_text == "-":
                log.info("Market suspended. Waiting...")
                await asyncio.sleep(1.0)
                continue

            team1_odd = float(team1_text)
            team2_odd = float(team2_text)

            log.info(f"{team1_name}: {team1_odd} | {team2_name}: {team2_odd} | Target: {target_odds}")

        except Exception as e:
            log.warning(f"Error reading odds: {e}. Retrying...")
            await asyncio.sleep(1.0)
            continue

        if not team1_bet_placed and team1_odd >= target_odds:
            log.info(f"TARGET HIT — {team1_name} back odd {team1_odd} >= {target_odds}")
            team1_bet_placed = True  # lock immediately — unknown outcome is still "placed"
            try:
                await place_bet(page, team1_row, bet_stake)
            except RuntimeError as e:
                log.warning(f"Team 1 bet outcome uncertain: {e}. Flag locked to prevent double bet.")

        if not team2_bet_placed and team2_odd >= target_odds:
            log.info(f"TARGET HIT — {team2_name} back odd {team2_odd} >= {target_odds}")
            team2_bet_placed = True
            try:
                await place_bet(page, team2_row, bet_stake)
            except RuntimeError as e:
                log.warning(f"Team 2 bet outcome uncertain: {e}. Flag locked to prevent double bet.")

        if team1_bet_placed and team2_bet_placed:
            log.info("Both bets placed. Monitoring complete.")
            return

        await asyncio.sleep(1.0)