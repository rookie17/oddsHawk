import asyncio
from playwright.async_api import async_playwright
import config
from utils.logger import get_logger
from monitor import login, navigate_to_ipl_match
from strategies.both_teams_same_odd import run as run_both_teams_same_odd
from strategies.cashout_strategy import run as run_cashout

log = get_logger("OddsHawk")


# ── Param collectors ────────────────────────────────────────────────────────

def _collect_generic_params(strategy: dict) -> dict:
    """Used for strategies whose params are a flat, ordered list."""
    params = {}
    for p in strategy["params"]:
        while True:
            try:
                params[p["key"]] = p["type"](input(p["prompt"]))
                break
            except ValueError:
                print(f"Invalid input. Expected {p['type'].__name__}.")
    return params


def _collect_cashout_params() -> dict:
    """
    Custom param collector for the cashout strategy.
    Handles branching: sub-mode determines which extra params to ask for.
    """
    print("\n  1. Bet + Cashout")
    print("  2. Just Cashout")
    while True:
        try:
            sub_mode = int(input("Select mode: "))
            if sub_mode in (1, 2):
                break
            print("Enter 1 or 2.")
        except ValueError:
            print("Invalid input.")

    team_name = input("Enter team name (used to find the match): ").strip()

    print("\n  Cashout trigger:")
    print("  1. When back odd reaches target")
    print("  2. When cashout amount reaches target")
    while True:
        try:
            mode_choice = int(input("Select cashout trigger: "))
            if mode_choice in (1, 2):
                cashout_mode = "odds" if mode_choice == 1 else "amount"
                break
            print("Enter 1 or 2.")
        except ValueError:
            print("Invalid input.")

    label = "target back odd" if cashout_mode == "odds" else "target cashout amount"
    while True:
        try:
            cashout_target = float(input(f"Enter {label}: "))
            break
        except ValueError:
            print("Invalid input. Expected a number.")

    params = {
        "sub_mode": sub_mode,
        "team_name": team_name,
        "cashout_mode": cashout_mode,
        "cashout_target": cashout_target,
    }

    if sub_mode == 1:
        while True:
            try:
                params["bet_stake"] = float(input("Enter bet stake amount: "))
                break
            except ValueError:
                print("Invalid input.")
        while True:
            try:
                params["bet_odds"] = float(input("Enter back odd at which to place the bet: "))
                break
            except ValueError:
                print("Invalid input.")

    return params


# ── Strategy registry ────────────────────────────────────────────────────────

STRATEGIES = [
    {
        "name": "Place bet on both teams at same odd",
        "run": run_both_teams_same_odd,
        # default_navigate=True means main.py calls navigate_to_ipl_match before run()
        "default_navigate": True,
        "params": [
            {"key": "target_odds", "prompt": "Enter target back odd (e.g. 2.1): ", "type": float},
            {"key": "bet_stake",   "prompt": "Enter stake amount (e.g. 100): ",     "type": float},
        ],
    },
    {
        "name": "Cashout strategy (Bet+Cashout or Just Cashout)",
        "run": run_cashout,
        # default_navigate=False — cashout strategy navigates internally using team name
        "default_navigate": False,
        "collect_params_fn": _collect_cashout_params,
    },
]


# ── Menu ─────────────────────────────────────────────────────────────────────

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
    """
    Dispatches to a strategy-specific collector if one is defined,
    otherwise uses the generic flat-list collector.
    """
    if "collect_params_fn" in strategy:
        return strategy["collect_params_fn"]()
    return _collect_generic_params(strategy)


# ── Entry point ───────────────────────────────────────────────────────────────

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

        # Only run the default IPL navigation for strategies that need it.
        # Strategies with default_navigate=False handle their own navigation internally.
        if strategy.get("default_navigate", True):
            await navigate_to_ipl_match(page)

        await strategy["run"](page, params)

        await browser.close()
        log.info("Browser closed. Done.")


asyncio.run(run())