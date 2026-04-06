from playwright.async_api import Page
import asyncio
import config
from utils.logger import get_logger

log = get_logger("Monitor")


async def monitor_site(page: Page) -> None:
    await _login(page)
    await _navigate_to_ipl_match(page)
    await _monitor_odds(page)


async def _login(page: Page) -> None:
    log.info("Starting login sequence...")

    username_field = page.locator('input[name="User Name"]')
    await username_field.wait_for(state="visible")
    log.info("Login form is visible.")

    await username_field.fill(config.USERNAME)
    log.info("Username entered.")

    password_field = page.locator('input[name="Password"]')
    await password_field.fill(config.PASSWORD)
    log.info("Password entered.")

    submit_button = page.locator('button[type="submit"].btn-login')
    await submit_button.click()
    log.info("Login button clicked. Waiting for redirect...")

    try:
        await page.wait_for_url("**/home**", timeout=10_000)
        log.info(f"Login successful. Landed on: {page.url}")
    except Exception:
        log.error(f"Login failed — still on: {page.url}")
        raise

async def _navigate_to_ipl_match(page: Page) -> None:
    log.info("Scanning home page for IPL matches...")

    all_match_links = page.locator("table.coupon-table tbody tr a.text-dark")
    await all_match_links.first.wait_for(state="visible")

    count = await all_match_links.count()
    log.info(f"Found {count} total matches on home page.")

    for i in range(count):
        link = all_match_links.nth(i)
        text = (await link.inner_text()).strip()

        parent_row = link.locator("xpath=ancestor::tr")
        is_virtual = await parent_row.locator("img.cardgame-icon").count() > 0
        if is_virtual:
            continue

        for team in config.IPL_TEAMS:
            if team.lower() in text.lower():
                log.info(f"IPL match found: '{text}'")
                await link.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.locator(".back.lock").first.wait_for(state="visible", timeout=30_000)
                log.info(f"Navigated to match page: {page.url}")
                return

    log.warning("No IPL match found on the home page today.")


async def _monitor_odds(page: Page) -> None:
    log.info(f"Starting odds monitor. Target back odd: {config.TARGET_ODDS}")

    # Find the .table-body that contains .back.lock — this is always the match odds block.
    # Fancy and bookmaker sections never have .back.lock elements.
    match_odds_table = page.locator(".table-body", has=page.locator(".back.lock")).first

    team1_row = match_odds_table.locator(".table-row").nth(0)
    team2_row = match_odds_table.locator(".table-row").nth(1)

    team1_name = (await team1_row.locator(".team-name b").first.inner_text()).strip()
    team2_name = (await team2_row.locator(".team-name b").first.inner_text()).strip()
    log.info(f"Monitoring: [{team1_name}] vs [{team2_name}]")

    team1_odd_locator = team1_row.locator(".back.lock .odd")
    team2_odd_locator = team2_row.locator(".back.lock .odd")

    while True:
        try:
            team1_text = (await team1_odd_locator.inner_text()).strip()
            team2_text = (await team2_odd_locator.inner_text()).strip()

            if team1_text == "-" or team2_text == "-":
                log.info("Market suspended. Waiting...")
                await asyncio.sleep(config.POLL_INTERVAL_SECONDS)
                continue

            team1_odd = float(team1_text)
            team2_odd = float(team2_text)

            log.info(f"{team1_name}: {team1_odd} | {team2_name}: {team2_odd} | Target: {config.TARGET_ODDS}")

            if team1_odd >= config.TARGET_ODDS:
                log.info(f"TARGET HIT — {team1_name} back odd {team1_odd} >= {config.TARGET_ODDS}")

            if team2_odd >= config.TARGET_ODDS:
                log.info(f"TARGET HIT — {team2_name} back odd {team2_odd} >= {config.TARGET_ODDS}")

        except Exception as e:
            log.warning(f"Error reading odds: {e}. Retrying...")

        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)