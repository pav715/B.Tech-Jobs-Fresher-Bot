import os

# ── Telegram ─────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8714105853:AAEBU3JWHAV8mk17MjSLTYh8W2QO2I-1cts")
CHAT_ID   = os.environ.get("CHAT_ID", "-1003539101161")

# ── Search keywords (B.Tech fresher — IT + core engineering) ─────────
# 16 keywords x 7 locations = 112 combinations (kept under ~120 so the
# GitHub Actions job finishes inside its 8-minute timeout).
KEYWORDS = [
    # Software / IT fresher roles
    "Software Engineer Fresher",
    "Graduate Engineer Trainee",
    "Junior Software Developer",
    "Associate Software Engineer",
    "SDE 1",
    "Trainee Engineer",
    "Java Fresher",
    "Python Fresher",
    "Web Developer Fresher",
    "Test Engineer Fresher",
    "Support Engineer Fresher",
    "DevOps Fresher",
    "Data Analyst Fresher",
    "Entry Level Software Engineer",
    # Core engineering fresher roles (ECE/EEE/Mechanical/Civil)
    "Graduate Trainee",
    "Junior Engineer",
]

# ── Locations (South India + Remote) ──────────────────────────────────
# Bengaluru covers Bangalore (same city on job boards); Hyderabad covers
# Telangana/Secunderabad; Remote covers pan-India work-from-home roles.
LOCATIONS = [
    "Hyderabad",
    "Bengaluru",
    "Chennai",
    "Coimbatore",
    "Kochi",
    "Visakhapatnam",
    "Remote",
]

# ── Timing ────────────────────────────────────────────────────────────
CHECK_INTERVAL_MINUTES = 10   # Check every 10 minutes
