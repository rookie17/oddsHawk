from playwright.async_api import Page
import config
from utils.logger import get_logger

log = get_logger("Monitor")


async def monitor_site(page: Page) -> None:
    await _login(page)
    log.info("Login complete. Odds monitoring will be wired up next.")


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
        log.info(f"✅ Login successful. Landed on: {page.url}")
    except Exception:
        log.error(
            f"❌ Login failed — still on: {page.url}\n"
            "Possible causes: wrong credentials, OTP prompt, CAPTCHA, or slow network."
        )
        raise