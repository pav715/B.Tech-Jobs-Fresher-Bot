# B.Tech Jobs Fresher Bot — Telegram

Automatically posts the latest **B.Tech fresher job openings** to Telegram every 5 minutes.

## 🎯 Target

- **Degree:** B.Tech only
- **Specializations:** CSE, ECE, EEE
- **Experience:** 0-1 years (freshers only)
- **Location:** Hyderabad, India
- **Frequency:** Every 5 minutes, 24/7

## 🔍 What We Search

### CSE (Computer Science & Engineering)
- AI & ML roles
- Data Science roles
- Cyber Security roles
- Software Engineer / Developer roles
- Python, Java, Full Stack, Web Developer roles

### ECE (Electronics & Communication Engineering)
- Embedded Systems
- VLSI
- Network Engineer roles

### EEE (Electrical & Electronics Engineering)
- Power Systems
- Electrical Engineer roles

## 📱 How It Works

1. **Every 5 minutes:** Bot fetches latest job postings from LinkedIn
2. **Filters applied:** Only B.Tech + Fresher (0-1 yrs) + Hyderabad
3. **Posts to Telegram:** Jobs are posted to the channel automatically
4. **No duplicates:** Uses job ID tracking to prevent re-posting

## ⚙️ Setup

### 1. Create GitHub Secrets

In your GitHub repo settings, add:
- `BOT_TOKEN` — Your Telegram Bot Token
- `BTECH_CHAT_ID` — Your B.Tech jobs channel ID (Private Group/Channel)

### 2. Push Code to GitHub

This bot runs on GitHub Actions (free tier).

### 3. Enable Workflow

GitHub Actions should auto-run the workflow every 5 minutes.

### 4. First Run

Manual trigger via GitHub Actions UI, then bot self-perpetuates.

## 📊 Files

- `config.py` — Keywords, locations, timing
- `scraper.py` — LinkedIn HTML parser
- `sender.py` — Telegram message formatter
- `bot.py` — Main bot logic + failed run recovery
- `.github/workflows/bot.yml` — GitHub Actions workflow
- `requirements.txt` — Python dependencies

## ✅ Features

- ✅ Only fresher jobs (0-1 years experience)
- ✅ B.Tech specializations only (CSE/ECE/EEE)
- ✅ Hyderabad location filter
- ✅ No duplicates across runs
- ✅ Dynamic time window (catches missed jobs if run fails)
- ✅ Silent if no new jobs (no spam)
- ✅ 24/7 automatic operation
- ✅ Self-healing (failed run recovery)
