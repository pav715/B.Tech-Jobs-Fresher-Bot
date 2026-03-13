"""
Job scraper — LinkedIn B.Tech Fresher Jobs Hyderabad
Filters for: CSE/ECE/EEE Freshers Only, Hyderabad only
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests
import hashlib
import re
import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import config

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
})

FRESHER_PATTERN = re.compile(
    r"\b(fresher|entry\s*level|graduate|new\s*graduate|recent\s*graduate|"
    r"campus\s*hire|trainee|0\s*years|0-1\s*year|less\s*than\s*1\s*year|first\s*job|"
    r"no\s*experience|zero\s*experience)\b",
    re.IGNORECASE,
)

# Pattern to REJECT jobs with experience requirement > 1 year
REJECT_EXPERIENCE_PATTERN = re.compile(
    r"\b(\d+\s*\+?\s*years?|2\s*years?|3\s*years?|4\s*years?|5\s*years?|"
    r"senior|mid\s*level|intermediate|experienced|professional with)",
    re.IGNORECASE,
)

# B.Tech pattern (CSE/ECE/EEE only)
BTECH_PATTERN = re.compile(
    r"\b(b\.?tech|be|cse|ece|eee|computer\s*science|electronics|electrical|"
    r"embedded|vlsi|power\s*systems|ai\s*ml|data\s*science|cyber\s*security|"
    r"software\s*engineer|software\s*developer|python|java|full\s*stack|web\s*developer)\b",
    re.IGNORECASE,
)

LOCATION_PATTERN = re.compile(
    r"\b(hyderabad|hyd|telangana|secunderabad|cyberabad)\b",
    re.IGNORECASE,
)


def job_id(url, title, company):
    raw = f"{url}{title}{company}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _delay():
    time.sleep(random.uniform(0.2, 0.5))  # Reduced for GitHub Actions


def _is_fresher_job(title, description):
    """Check if job is ONLY for freshers (0-1 years exp). Reject any experienced roles."""
    text = f"{title} {description}".lower()

    # MUST match fresher keywords
    if not FRESHER_PATTERN.search(text):
        return False

    # REJECT if it requires > 1 year experience
    if REJECT_EXPERIENCE_PATTERN.search(text):
        return False

    return True


def _is_btech_job(title, description):
    """Check if job is for B.Tech (CSE/ECE/EEE)."""
    text = f"{title} {description}".lower()
    return bool(BTECH_PATTERN.search(text))


def _has_excessive_experience(title, description):
    """Check if job requires more than 1 year experience. Reject if true."""
    text = f"{title} {description}".lower()
    return bool(REJECT_EXPERIENCE_PATTERN.search(text))


def _has_location(location_str):
    """Check if location contains Hyderabad/Telangana."""
    if not location_str:
        return False
    return bool(LOCATION_PATTERN.search(location_str))


# ── LinkedIn Jobs (via HTML search) ──────────────────────────────────
def fetch_linkedin_jobs():
    """
    LinkedIn jobs search for B.Tech freshers in Hyderabad.
    Uses public search URLs with base-card HTML selector.
    """
    jobs = []
    search_terms = [
        "B.Tech+fresher+Hyderabad",
        "CSE+fresher+Hyderabad",
        "Software+engineer+fresher+Hyderabad",
    ]

    for search_term in search_terms:
        try:
            # LinkedIn public search URL with strict fresher filters
            # f_E=1: Entry level only
            # f_EL=1: All education levels (needed to match graduates)
            # f_TPR=r86400: Posted in last 24h
            url = (
                f"https://www.linkedin.com/jobs/search/"
                f"?keywords={search_term}"
                f"&location=Hyderabad"
                f"&f_E=1"  # STRICT: Entry level experience filter
                f"&f_EL=1"  # Include all education levels (UG, PG, diploma)
                f"&f_TPR=r86400"  # Posted in last 24h
            )

            r = SESSION.get(url, timeout=15)
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.content, "html.parser")

            # Find all job cards using base-card class
            for card in soup.find_all("div", class_="base-card"):
                try:
                    # Extract title
                    title_elem = card.find("h3", class_="base-search-card__title")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)

                    # Extract company
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"

                    # Extract location
                    location_elem = card.find("span", class_="job-search-card__location")
                    location = location_elem.get_text(strip=True) if location_elem else ""

                    # Extract URL
                    link_elem = card.find("a", class_="base-card__full-link")
                    job_url = link_elem.get("href", "") if link_elem else ""

                    # Extract posted date (from time element's datetime attribute)
                    date_elem = card.find("time")
                    if date_elem and date_elem.get("datetime"):
                        posted_date = date_elem.get("datetime")
                    else:
                        # If no time element, mark as current time (will pass 5-min filter)
                        posted_date = datetime.now().isoformat()

                    # Get description from card text
                    description = card.get_text(strip=True)[:500]

                    if not title or not job_url:
                        continue

                    # STRICT FILTER: Only 0-1 years experience
                    if not _is_fresher_job(title, description):
                        continue

                    # REJECT: Any job requiring > 1 year experience
                    if _has_excessive_experience(title, description):
                        continue

                    # MUST be B.Tech related (CSE/ECE/EEE)
                    if not _is_btech_job(title, description):
                        continue

                    if not _has_location(location):
                        continue

                    job = {
                        "id": job_id(job_url, title, company),
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "source": "LinkedIn",
                        "description": description,
                        "posted": posted_date,
                    }
                    jobs.append(job)
                    _delay()
                except Exception:
                    continue

            _delay()
        except Exception as e:
            print(f"LinkedIn search '{search_term}' error: {e}")

    return jobs


# ── Aggregate All Jobs ────────────────────────────────────────────────
def fetch_all_jobs(minutes_back=5):
    """
    Fetch from LinkedIn only.
    Return jobs posted in the last N minutes (dynamic time window).
    If previous run failed, this will be > 5 minutes to catch missed jobs.

    Args:
        minutes_back: How many minutes back to fetch jobs from (default 5)
    """
    all_jobs = []

    print(f"Fetching LinkedIn B.Tech jobs from last {minutes_back} minutes...")
    all_jobs.extend(fetch_linkedin_jobs())

    # Filter jobs posted in last N minutes
    now = datetime.now()
    cutoff_time = now - timedelta(minutes=minutes_back)

    recent_jobs = []
    for job in all_jobs:
        try:
            posted_str = job.get("posted", "")
            if not posted_str:
                continue

            # Parse datetime - handle various formats
            try:
                # Try ISO format first
                posted_time = datetime.fromisoformat(posted_str.replace('Z', '+00:00'))
            except Exception:
                try:
                    # Try parsing as plain date (YYYY-MM-DD)
                    posted_time = datetime.fromisoformat(posted_str)
                except Exception:
                    # Skip if can't parse
                    continue

            # Keep only if posted after cutoff time
            if posted_time >= cutoff_time:
                recent_jobs.append(job)
        except Exception:
            continue

    # Deduplicate by ID
    seen_ids = set()
    unique_jobs = []
    for job in recent_jobs:
        if job["id"] not in seen_ids:
            seen_ids.add(job["id"])
            unique_jobs.append(job)

    # Sort by posted date (newest first)
    unique_jobs.sort(
        key=lambda x: x.get("posted", ""),
        reverse=True
    )

    print(f"Found {len(unique_jobs)} B.Tech fresher jobs posted in last {minutes_back} minutes")
    return unique_jobs
