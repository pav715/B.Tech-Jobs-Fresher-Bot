import os

# ── Telegram ─────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")  # Use same CHAT_ID as US Tax bot

# ── B.Tech Specializations (Telangana) ───────────────────────────────
# CSE: AI&ML, Data Science, Cyber Security, CS & Business Systems
# ECE: Electronics, Telematics, Embedded Systems
# EEE: Power Systems, Electrical Machines

KEYWORDS = [
    # ── CSE & Specializations ──
    "B.Tech CSE",
    "Computer Science",
    "CSE Fresher",
    "AI ML Fresher",
    "Data Science Fresher",
    "Cyber Security Fresher",
    "Software Engineer Fresher",
    "Software Developer Fresher",
    "Python Developer Fresher",
    "Java Developer Fresher",
    "Full Stack Fresher",
    "Web Developer Fresher",

    # ── ECE & Specializations ──
    "B.Tech ECE",
    "Electronics Communication Fresher",
    "Embedded Systems Fresher",
    "VLSI Fresher",
    "Hardware Engineer Fresher",
    "Network Engineer Fresher",

    # ── EEE & Specializations ──
    "B.Tech EEE",
    "Electrical Engineer Fresher",
    "Power Systems Fresher",
    "Electrical Fresher",

    # ── General B.Tech ──
    "B.Tech Fresher",
    "BE Fresher",
    "Engineering Fresher",
    "Graduate Engineer Trainee",
    "GET",
    "Campus Hire",
    "Entry Level Engineer",
]

# ── Locations (Hyderabad Only) ────────────────────────────────────────
LOCATIONS = [
    "Hyderabad",
    "Hyderabad India",
    "Telangana",
    "Secunderabad",
    "Cyberabad",
]

# ── Timing ────────────────────────────────────────────────────────────
CHECK_INTERVAL_MINUTES = 5   # Check every 5 minutes

# ── Workday ATS Companies ──────────────────────────────────────────────
WORKDAY_COMPANIES = []

# ── India Job Portals ─────────────────────────────────────────────────
INDIA_PORTALS = []

# ── Company Career Sites ──────────────────────────────────────────────
COMPANY_SITES = []
