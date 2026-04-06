from dotenv import load_dotenv
import os

load_dotenv()

SITE_URL = "https://play99exch.win/login"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

TARGET_ODDS = 2.50
POLL_INTERVAL_SECONDS = 1.0
HEADLESS = False
BET_STAKE = 100

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