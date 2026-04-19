import asyncio
from playwright.async_api import async_playwright
import config
from utils.logger import get_logger
from monitor import login, navigate_to_ipl_match
from strategies.both_teams_same_odd import run as run_both_teams_same_odd

log = get_logger("OddsHawk")

STRATEGIES = [
    {
        "name": "Place bet on both teams at same odd",
        "run": run_both_teams_same_odd,
        "params": [
            {"key": "target_odds", "prompt": "Enter target back odd (e.g. 2.1): ", "type": float},
            {"key": "bet_stake",   "prompt": "Enter stake amount (e.g. 100): ",     "type": float},
        ],
    },
]


def show_menu() -> int:
    print("\n=== OddsHawk ===")
    for i, strategy in enumerate(STRATEGIES, 1):
        print(f"{i}. {strategy['name']}")
    while True:
        try:
            choice = int(input("\nSelect a strategy: "))
            if 1 <= choice <= len(STRATEGIES):
                return choice - 1
            print(f"Enter a number between 1 and {len(STRATEGIES)}.")
        except ValueError:
            print("Invalid input. Enter a number.")


def collect_params(strategy: dict) -> dict:
    params = {}
    for p in strategy["params"]:
        while True:
            try:
                params[p["key"]] = p["type"](input(p["prompt"]))
                break
            except ValueError:
                print(f"Invalid input. Expected {p['type'].__name__}.")
    return params


async def run():
    strategy_index = show_menu()
    strategy = STRATEGIES[strategy_index]
    params = collect_params(strategy)

    log.info(f"Starting: {strategy['name']}")
    log.info(f"Params: {params}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        log.info("Browser launched.")

        page = await browser.new_page()
        await page.goto(config.SITE_URL)
        log.info(f"Opened: {config.SITE_URL}")

        await login(page)
        await navigate_to_ipl_match(page)
        await strategy["run"](page, params)

        await browser.close()
        log.info("Browser closed. Done.")


asyncio.run(run())