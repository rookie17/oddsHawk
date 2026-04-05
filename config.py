# config.py — All settings for OddsHawk in one place

# ── Site ──────────────────────────────────────────────────────────────────────
SITE_URL = "https://play99exch.win/login"

# ── Credentials ───────────────────────────────────────────────────────────────
# ⚠️  Never commit real credentials to git. This is fine for local dev.
#     Later we'll move these to a .env file and load with python-dotenv.
USERNAME = "99aaditya4244"
PASSWORD = "Play99Aadi*17"

# ── Odds logic ────────────────────────────────────────────────────────────────
TARGET_ODDS = 2.50          # Trigger bet when odds hit this value
POLL_INTERVAL_SECONDS = 1.0 # How often to re-check odds (seconds)

# ── Browser ───────────────────────────────────────────────────────────────────
HEADLESS = False            # False = visible window (easier to debug login issues)

IPL_TEAMS = [
    "Sunrisers Hyderabad",
    "Lucknow Super Giants",
    "Royal Challengers Bengaluru",
    "Chennai Super Kings",
    "Mumbai Indians",
    "Kolkata Knight Riders",
    "Delhi Capitals",
    "Rajasthan Royals",
    "Punjab Kings",
    "Gujarat Titans",
]