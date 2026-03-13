"""
B.Tech Jobs Fresher — Telegram Bot
Runs 24/7, checks every 5 minutes, sends only jobs posted in that 5-min window.
If previous run failed, fetches jobs from last successful run time.
Target: B.Tech freshers (CSE/ECE/EEE) in Hyderabad
"""
import json
import os
import time
import requests
from datetime import datetime
import config
from scraper import fetch_all_jobs
from sender import send_job

SEEN_FILE = "seen_jobs.json"
LOG_FILE = "bot.log"
LAST_RUN_FILE = "last_successful_run.txt"


def load_seen():
    """Load previously seen job IDs to prevent duplicates."""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_seen(seen_set):
    """Save seen job IDs. Keep only last 5000."""
    data = list(seen_set)[-5000:]
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)


def load_last_run_time():
    """Load timestamp of last successful run."""
    if os.path.exists(LAST_RUN_FILE):
        try:
            with open(LAST_RUN_FILE, "r") as f:
                return f.read().strip()
        except Exception:
            pass
    return None


def save_last_run_time(timestamp):
    """Save timestamp of successful run."""
    try:
        with open(LAST_RUN_FILE, "w") as f:
            f.write(timestamp)
    except Exception:
        pass


def log(msg):
    """Log message to both console and file with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def calculate_minutes_back():
    """Calculate how many minutes back to fetch jobs from."""
    last_run = load_last_run_time()

    if not last_run:
        # First run ever - fetch from last 5 minutes
        log("First run detected - fetching from last 5 minutes")
        return 5

    try:
        # Parse last successful run time
        last_time = datetime.fromisoformat(last_run)
        now = datetime.now()

        # Calculate minutes since last successful run
        minutes_diff = (now - last_time).total_seconds() / 60

        # Add 1 minute buffer to catch edge cases
        minutes_back = int(minutes_diff) + 1

        log(f"Last successful run was {minutes_diff:.1f} mins ago - fetching from last {minutes_back} minutes")
        return minutes_back
    except Exception as e:
        log(f"Error calculating time window: {e} - defaulting to 5 minutes")
        return 5


def run_cycle(seen):
    """Run one complete job search and posting cycle."""
    minutes_back = calculate_minutes_back()
    log(f"Checking for new B.Tech fresher jobs from LinkedIn...")

    try:
        jobs = fetch_all_jobs(minutes_back=minutes_back)
    except Exception as e:
        log(f"Scrape error: {e}")
        return False

    new_jobs = [j for j in jobs if j["id"] not in seen]

    if not new_jobs:
        log(f"No new jobs found. Total tracked: {len(seen)}")
        return True  # Still successful even if no jobs

    log(f"Found {len(new_jobs)} new B.Tech fresher jobs! Sending to Telegram...")

    sent = 0
    for job in new_jobs:
        try:
            ok = send_job(job)
            if ok:
                seen.add(job["id"])
                sent += 1
                log(f"  Sent: [{job['source']}] {job['title']} @ {job['company']} | {job['location']}")
            else:
                log(f"  Failed to send: {job['title']}")
        except Exception as e:
            log(f"  Error sending job: {e}")

    save_seen(seen)
    log(f"Done. Sent {sent} new B.Tech fresher jobs. Total tracked: {len(seen)}")
    return True


def main():
    """Main bot - single cycle execution for GitHub Actions."""
    log("=" * 70)
    log("  B.Tech Jobs Fresher — Telegram Bot")
    log("  TARGET: B.Tech Freshers (0-1 years) | FOCUS: CSE/ECE/EEE")
    log("  LOCATIONS: Hyderabad only")
    log(f"  CHECK INTERVAL: Every {config.CHECK_INTERVAL_MINUTES} minutes")
    log("=" * 70)

    if not config.BOT_TOKEN or not config.CHAT_ID:
        log("ERROR: BOT_TOKEN or CHAT_ID not set.")
        return False

    log("✅ Bot configured: BOT_TOKEN and CHAT_ID loaded")

    seen = load_seen()
    log(f"Loaded {len(seen)} previously seen jobs (no duplicates).")

    success = run_cycle(seen)

    if success:
        # Save timestamp of successful run
        current_time = datetime.now().isoformat()
        save_last_run_time(current_time)
        log("✅ Successful run completed. Timestamp saved.")
    else:
        log("❌ Run failed. Will retry with extended time window on next run.")

    log("Single-run cycle complete. Exiting.")
    return success


if __name__ == "__main__":
    main()
