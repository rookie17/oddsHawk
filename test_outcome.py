import asyncio
from playwright.async_api import async_playwright
from actions import _check_bet_outcome
from utils.logger import get_logger

log = get_logger("Test")

# Mimics the real div.card.my-bet DOM from play99exch
MOCK_HTML = """
<!DOCTYPE html>
<html>
<body>
<div class="card m-b-10 my-bet">
  <div class="card-header"><h6 class="card-title d-inline-block">My Bet</h6></div>
  <div class="card-body">
    <app-d-bet-list>
      <table class="coupon-table table table-borderedless">
        <thead>
          <tr><th>Nation</th><th class="text-right">Odds</th><th class="text-center">Stake</th></tr>
        </thead>
        <!-- Starts empty, just like real site -->
        <tr id="no-records"><td colspan="3" class="text-center">No records Found</td></tr>
      </table>
    </app-d-bet-list>
  </div>
</div>
</body>
</html>
"""

# JS that injects a tr.back row — simulates what the site does after bet is accepted
INJECT_BET_ROW_JS = """
(teamName) => {
    const table = document.querySelector('div.card.my-bet table.coupon-table');
    const noRecords = document.getElementById('no-records');
    if (noRecords) noRecords.remove();

    const row = document.createElement('tr');
    row.className = 'back ng-star-inserted';
    row.innerHTML = `
        <td style="width:60%">${teamName} </td>
        <td class="text-right">2.52</td>
        <td class="text-center">100</td>
    `;
    table.appendChild(row);
}
"""

async def test_my_bet_table_detection():
    """
    Simulates: submit clicked → toast never appears → My Bet table row appears after 2s
    Expected: _check_bet_outcome detects the row and returns without raising
    """
    team_name = "Sunrisers Hyderabad"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_content(MOCK_HTML)
        log.info("Page loaded. My Bet table is empty (No records Found).")

        # Inject the bet row after 2 seconds in background — simulates async DOM update
        # asyncio.create_task schedules this to run concurrently while _check_bet_outcome polls
        async def inject_after_delay():
            await asyncio.sleep(2.0)
            await page.evaluate(INJECT_BET_ROW_JS, team_name)
            log.info(f"[Simulator] Injected tr.back row for '{team_name}' into My Bet table.")

        asyncio.create_task(inject_after_delay())

        try:
            await _check_bet_outcome(page, team_name)
            log.info("PASS — Bet confirmed via My Bet table.")
        except RuntimeError as e:
            log.error(f"FAIL — {e}")

        await browser.close()


async def test_toast_success_detection():
    """
    Simulates: toast-success appears after 1s
    Expected: _check_bet_outcome returns immediately on toast
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(MOCK_HTML)
        log.info("Page loaded. No toast yet.")

        async def inject_toast():
            await asyncio.sleep(1.0)
            await page.evaluate("""
                const t = document.createElement('div');
                t.className = 'toast-success';
                t.innerHTML = '<div class="toast-message">Bet Placed Successfully!!</div>';
                document.body.appendChild(t);
            """)
            log.info("[Simulator] Injected toast-success.")

        asyncio.create_task(inject_toast())

        try:
            await _check_bet_outcome(page, "Sunrisers Hyderabad")
            log.info("PASS — Bet confirmed via toast.")
        except RuntimeError as e:
            log.error(f"FAIL — {e}")

        await browser.close()


async def test_timeout_no_confirmation():
    """
    Simulates: nothing appears — neither toast nor My Bet row
    Expected: RuntimeError raised after 5s timeout
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(MOCK_HTML)
        log.info("Page loaded. Nothing will appear.")

        try:
            await _check_bet_outcome(page, "Sunrisers Hyderabad")
            log.error("FAIL — Should have timed out but didn't.")
        except RuntimeError as e:
            log.info(f"PASS — Correctly timed out: {e}")

        await browser.close()


async def main():
    log.info("=== TEST 1: My Bet table detection (toast absent) ===")
    await test_my_bet_table_detection()

    log.info("\n=== TEST 2: Toast success detection ===")
    await test_toast_success_detection()

    log.info("\n=== TEST 3: Timeout — nothing confirms ===")
    await test_timeout_no_confirmation()


asyncio.run(main())