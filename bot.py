"""
B.Tech Jobs Fresher — Telegram Bot
Runs every 5 minutes via GitHub Actions.
Sends only new jobs — no duplicates, no backlog on first run.
"""
import json
import os
import time
import requests
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import config
from scraper import fetch_all_jobs
from sender import send_job

SEEN_FILE     = "seen_jobs.json"
LOG_FILE      = "bot.log"


def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_seen(seen_set):
    data = list(seen_set)[-5000:]
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)


def log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── Date helpers (same as US Tax bot) ─────────────────────────────────
def _is_within_days(job, days):
    """Return True if job was posted within last `days` days."""
    today  = datetime.now().date()
    cutoff = today - timedelta(days=days)

    posted  = job.get("posted") or ""
    fetched = job.get("fetched_at") or ""

    for value in (posted, fetched):
        if not value:
            continue
        iso = value.replace("Z", "").split("+")[0]
        try:
            dt = datetime.fromisoformat(iso)
            if cutoff <= dt.date() <= today:
                return True
        except Exception:
            pass

    # RFC822 (Indeed pubDate format)
    if posted:
        try:
            dt = parsedate_to_datetime(posted)
            if cutoff <= dt.date() <= today:
                return True
        except Exception:
            pass

    return False


def _location_allowed(loc_str):
    loc     = (loc_str or "").lower()
    allowed = [x.lower() for x in config.LOCATIONS]
    if not allowed or not loc:
        return True
    return any(a in loc for a in allowed)


# ── First run: mark existing jobs as seen (no backlog spam) ────────────
def initialize_seen_if_empty(seen):
    if seen:
        return seen
    log("First run: preloading existing jobs as seen — only NEW jobs will be posted.")
    try:
        jobs = fetch_all_jobs()
        for j in jobs:
            if "id" in j:
                seen.add(j["id"])
        save_seen(seen)
        log(f"Preload done. {len(seen)} jobs marked as seen.")
    except Exception as e:
        log(f"Preload error: {e}")
    return seen


# ── One scrape cycle ───────────────────────────────────────────────────
def run_cycle(seen):
    log("Checking for new B.Tech fresher jobs from LinkedIn...")
    try:
        jobs = fetch_all_jobs()
    except Exception as e:
        log(f"Scrape error: {e}")
        return False

    # Jobs from last 2 days in allowed locations
    recent = [j for j in jobs if _is_within_days(j, 2) and _location_allowed(j.get("location", ""))]
    candidates = recent if recent else [j for j in jobs if _location_allowed(j.get("location", ""))]

    new_jobs = [j for j in candidates if j["id"] not in seen]

    if not new_jobs:
        log(f"No new jobs found. Total tracked: {len(seen)}")
        return True

    log(f"Found {len(new_jobs)} new jobs! Sending to Telegram...")
    sent = 0
    for job in new_jobs:
        try:
            ok = send_job(job)
            if ok:
                seen.add(job["id"])
                sent += 1
                log(f"  Sent: [{job['source']}] {job['title']} @ {job['company']} | {job['location']}")
            else:
                log(f"  Failed: {job['title']}")
        except Exception as e:
            log(f"  Error: {e}")

    save_seen(seen)
    log(f"Done. Sent {sent} new jobs. Total tracked: {len(seen)}")
    return True


def main():
    log("=" * 60)
    log("  B.Tech Jobs Fresher - Telegram Bot")
    log("  TARGET: B.Tech Freshers | LOCATION: Hyderabad")
    log(f"  CHECK INTERVAL: Every {config.CHECK_INTERVAL_MINUTES} minutes")
    log("=" * 60)

    if not config.BOT_TOKEN or not config.CHAT_ID:
        log("ERROR: BOT_TOKEN or CHAT_ID not set.")
        return False

    seen = load_seen()
    log(f"Loaded {len(seen)} previously seen jobs.")

    seen = initialize_seen_if_empty(seen)

    success = run_cycle(seen)

    log("Single-run cycle complete. Exiting.")
    return success


if __name__ == "__main__":
    main()
