# config.py — All settings for OddsHawk in one place

# The betting site we'll monitor
SITE_URL = "https://play99exch.win/login"  # we'll replace this with the real URL later

# The odds value we want to trigger on
TARGET_ODDS = 2.50

# How often to check the odds (in seconds)
POLL_INTERVAL_SECONDS = 1.0

# Show the browser window while running (True = visible, False = hidden)
HEADLESS = False