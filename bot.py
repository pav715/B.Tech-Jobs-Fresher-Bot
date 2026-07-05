"""
B.Tech Jobs Fresher — Telegram Bot
Runs every 5 minutes via GitHub Actions.
Sends only new jobs — no duplicates, no backlog on first run.
"""
import json
import os
import time
import sys
import requests
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import config

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from scraper import fetch_all_jobs
from sender import send_job

SEEN_FILE     = "seen_jobs.json"
STATE_FILE    = "bot_state.json"
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


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_run_at": ""}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── Date helpers ──────────────────────────────────────────────────────
def _is_today(job):
    """Return True if job was posted today."""
    today = datetime.now().date()
    posted  = job.get("posted") or ""
    fetched = job.get("fetched_at") or ""

    for value in (posted, fetched):
        if not value:
            continue
        iso = value.replace("Z", "").split("+")[0]
        try:
            dt = datetime.fromisoformat(iso)
            if dt.date() == today:
                return True
        except Exception:
            pass

    # RFC822 (Indeed pubDate format)
    if posted:
        try:
            dt = parsedate_to_datetime(posted)
            if dt.date() == today:
                return True
        except Exception:
            pass

    return False


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


def _job_datetime(job):
    """Best-effort datetime for when a job was posted/fetched. Returns None if unknown."""
    posted  = job.get("posted") or ""
    fetched = job.get("fetched_at") or ""
    for value in (posted, fetched):
        if not value:
            continue
        iso = str(value).replace("Z", "").split("+")[0]
        try:
            return datetime.fromisoformat(iso)
        except Exception:
            pass
        try:
            return parsedate_to_datetime(value).replace(tzinfo=None)
        except Exception:
            pass
    return None


# ── First run: mark existing jobs as seen (no backlog spam) ────────────
def initialize_seen_if_empty(seen):
    if seen:
        return seen
    log("First run: preloading existing jobs as seen — only NEW jobs will be posted.")
    try:
        jobs = fetch_all_jobs()
        for j in jobs:
            seen.add(_dedup_key(j))
        save_seen(seen)
        log(f"Preload done. {len(seen)} jobs marked as seen.")
    except Exception as e:
        log(f"Preload error: {e}")
    return seen


# ── Title-based dedup key (blocks the same job even if LinkedIn changes its URL) ──
def _dedup_key(job):
    title   = (job.get("title") or "").lower().strip()
    company = (job.get("company") or "").lower().strip()
    return f"{title}|{company}"


# ── One scrape cycle ───────────────────────────────────────────────────
def run_cycle(seen, cutoff_dt):
    log("Checking for new B.Tech fresher jobs from LinkedIn...")
    try:
        jobs = fetch_all_jobs()
    except Exception as e:
        log(f"Scrape error: {e}")
        return False

    # Location filter first.
    located = [j for j in jobs if _location_allowed(j.get("location", ""))]

    # Time window: only jobs posted/fetched AFTER the last successful run.
    # Jobs with a known timestamp older than cutoff are skipped; jobs with an
    # unknown timestamp fall back to the dedup check so nothing is lost silently.
    fresh = []
    for j in located:
        dt = _job_datetime(j)
        if dt is None or dt >= cutoff_dt:
            fresh.append(j)

    # Dedup by TITLE+COMPANY, not by URL/id — same job never posts twice,
    # even when it stays live on LinkedIn all week with a new URL each scrape.
    new_jobs = [j for j in fresh if _dedup_key(j) not in seen]

    if not new_jobs:
        log(f"No new jobs found. Total tracked: {len(seen)}")
        return True

    log(f"Found {len(new_jobs)} new jobs! Sending to Telegram...")
    sent = 0
    for job in new_jobs:
        try:
            ok = send_job(job)
            if ok:
                seen.add(_dedup_key(job))
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

    # Time window: only send jobs that appeared since the last successful run.
    state = load_state()
    last_run = state.get("last_run_at", "")
    now = datetime.now()
    if last_run:
        try:
            cutoff_dt = datetime.fromisoformat(last_run)
        except Exception:
            cutoff_dt = now - timedelta(minutes=45)
    else:
        # First run ever: only look at the last 45 minutes so we don't dump a week of backlog.
        cutoff_dt = now - timedelta(minutes=45)
    log(f"Window: sending jobs posted after {cutoff_dt.isoformat()}")

    seen = initialize_seen_if_empty(seen)

    success = run_cycle(seen, cutoff_dt)

    # Save this run's time only if the cycle succeeded (so a failed scrape
    # doesn't advance the window and skip jobs).
    if success:
        state["last_run_at"] = now.isoformat()
        save_state(state)

    log("Single-run cycle complete. Exiting.")
    return success


if __name__ == "__main__":
    main()
