from playwright.async_api import Page
from utils.logger import get_logger

log = get_logger("Actions")

async def place_bet(page: Page) -> None:
    # Real click sequence will go here once we have a target site
    log.info("place_bet() called — no action defined yet.")