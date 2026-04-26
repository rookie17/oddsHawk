from playwright.async_api import Page
import asyncio
import config
from utils.logger import get_logger

log = get_logger("Monitor")


async def monitor_site(page: Page) -> None:
    await login(page)
    await navigate_to_ipl_match(page)


async def login(page: Page) -> None:
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


async def navigate_to_ipl_match(page: Page) -> None:
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


async def navigate_to_any_match(page: Page, team_name: str) -> None:
    """
    Scans the home page for the first match containing team_name (case-insensitive).
    Used by strategies that are not IPL-specific.
    Skips virtual/esports matches the same way navigate_to_ipl_match does.
    """
    log.info(f"Scanning home page for match with team: '{team_name}'...")

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

        if team_name.lower() in text.lower():
            log.info(f"Match found: '{text}'")
            await link.click()
            await page.wait_for_load_state("domcontentloaded")
            await page.locator(".back.lock").first.wait_for(state="visible", timeout=30_000)
            log.info(f"Navigated to match page: {page.url}")
            return

    raise RuntimeError(f"No match found containing team name: '{team_name}'")