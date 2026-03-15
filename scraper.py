"""
Job scraper — B.Tech Jobs Fresher
Sources: LinkedIn public API, Naukri API, Indeed RSS
Logic: Search by B.Tech-group keywords. Job role can be ANYTHING.
       Only check job DESCRIPTION for fresher/0-1 exp indicators.
"""
import requests
import hashlib
import re
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def job_id(url, title, company):
    """Unique fingerprint for a job — used to detect duplicates."""
    raw = f"{url}{title}{company}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def delay():
    time.sleep(random.uniform(0.3, 0.7))


# ── Fresher check — applied to JOB DESCRIPTION only ───────────────
# Job ROLE/TITLE can be anything — companies put education in description
FRESHER_DESC_PATTERN = re.compile(
    r"""
    fresher                         # fresher
    | fresh\s*graduate              # fresh graduate
    | entry[\s\-]*level             # entry level / entry-level
    | any\s*graduate                # any graduate
    | recent\s*graduate             # recent graduate
    | 0[\s\-]*1\s*year              # 0-1 year / 0 - 1 year
    | 0[\s\-]*1\s*yr                # 0-1 yr
    | exp[:\s]*0[\s\-]*1            # exp: 0-1 / exp 0-1
    | exp[:\s]*0\s*year             # exp: 0 year
    | exp[:\s]*0\s*yr               # exp: 0 yr
    | experience[:\s]*0[\s\-]*1     # experience: 0-1
    | experience[:\s]*0\s*year      # experience: 0 year
    | \b0\s*year[s]?\s*exp          # 0 years exp
    | \b0\s*yr[s]?\s*exp            # 0 yrs exp
    | no\s*experience\s*required    # no experience required
    | without\s*experience          # without experience
    | trainee                       # trainee
    | campus\s*hire                 # campus hire
    | campus\s*recruit              # campus recruit
    | batch\s*20(2[3-9]|[3-9]\d)   # batch 2023/2024/2025 etc
    | 2024\s*batch                  # 2024 batch
    | 2025\s*batch                  # 2025 batch
    | passed\s*out\s*20(2[3-9])     # passed out 2023/2024/2025
    | b\.?tech\b                    # B.Tech
    | b\.?\s*e\.?\b                 # BE
    | c\.?s\.?e\.?\b                # CSE
    | e\.?c\.?e\.?\b                # ECE
    | e\.?e\.?e\.?\b                # EEE
    | \bit\b                        # IT
    | computer\s*science            # computer science
    | information\s*technology      # information technology
    | electronics                   # electronics
    | electrical\s*engineering      # electrical engineering
    | mechanical\s*engineering      # mechanical engineering
    | civil\s*engineering           # civil engineering
    | any\s*engineering             # any engineering
    | engineering\s*graduate        # engineering graduate
    | m\.?tech\b                    # M.Tech
    | bachelor['\s]*s?\s*degree     # bachelor's degree
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Reject ONLY if description clearly states 2+ years required
# Must NOT reject: "0-1 years", "1 year", "less than 1 year"
REJECT_EXP_PATTERN = re.compile(
    r"""
    \b([2-9]|\d{2,})\s*\+?\s*years?\s*(of\s*)?(experience|exp)\b  # 2+ years experience
    | \b([2-9]|\d{2,})\s*\+?\s*yrs?\s*(of\s*)?(experience|exp)\b  # 2+ yrs experience
    | minimum\s*[2-9]\s*years?                                      # minimum 2 years
    | at\s*least\s*[2-9]\s*years?                                   # at least 2 years
    | \bsenior\b                                                     # senior
    | \blead\b                                                       # lead
    | \bmanager\b                                                    # manager
    """,
    re.IGNORECASE | re.VERBOSE,
)

LOCATION_PATTERN = re.compile(
    r"\b(hyderabad|hyd|telangana|secunderabad|cyberabad)\b",
    re.IGNORECASE,
)


def _is_fresher_desc(description):
    """
    Check job DESCRIPTION for fresher/0-1 exp / B.Tech indicators.
    Job title/role is NOT checked — can be anything.
    Returns True if description indicates fresher/0-1 exp role for B.Tech.
    """
    if not description:
        return False
    if not FRESHER_DESC_PATTERN.search(description):
        return False
    if REJECT_EXP_PATTERN.search(description):
        return False
    return True


def _has_location(location_str):
    if not location_str:
        return False
    return bool(LOCATION_PATTERN.search(location_str))


# ── LinkedIn: fetch job description from job detail page ──────────
def _fetch_linkedin_desc(job_url):
    """Fetch LinkedIn job description text from the public job page."""
    try:
        r = requests.get(job_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        desc_tag = soup.find("div", class_=re.compile(r"description|show-more-less-html", re.I))
        if desc_tag:
            return desc_tag.get_text(separator=" ", strip=True)
    except Exception:
        pass
    return ""


# ── LINKEDIN ──────────────────────────────────────────────────────
def scrape_linkedin(keyword, location):
    jobs = []
    try:
        kw  = keyword.replace(" ", "%20")
        loc = location.replace(" ", "%20")
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
            f"keywords={kw}&location={loc}&f_TPR=r604800"
            f"&sortBy=DD&start=0"
        )
        r    = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        for card in soup.find_all("li")[:20]:
            try:
                title    = card.find("h3").get_text(strip=True) if card.find("h3") else ""
                company  = card.find("h4").get_text(strip=True) if card.find("h4") else ""
                loc_tag  = card.find("span", class_=re.compile("job-search-card__location"))
                loc_str  = loc_tag.get_text(strip=True) if loc_tag else location
                link_tag = card.find("a", href=True)
                link     = link_tag["href"].split("?")[0] if link_tag else ""
                time_tag = card.find("time")
                posted   = time_tag["datetime"] if time_tag and time_tag.get("datetime") else ""

                if not title or not link:
                    continue
                if not _has_location(loc_str):
                    continue

                # Fetch description and check for fresher/B.Tech indicators
                desc = _fetch_linkedin_desc(link)
                if not _is_fresher_desc(desc):
                    continue

                delay()
                jobs.append({
                    "id":       job_id(link, title, company),
                    "title":    title,
                    "company":  company,
                    "location": loc_str,
                    "url":      link,
                    "posted":   posted,
                    "source":   "LinkedIn",
                    "fetched_at": datetime.now().isoformat(),
                })
            except Exception:
                pass
    except Exception as e:
        print(f"  [LinkedIn] Error ({keyword}/{location}): {e}")
    return jobs


# ── NAUKRI ────────────────────────────────────────────────────────
def scrape_naukri(keyword, location):
    jobs = []
    try:
        kw  = keyword.replace(" ", "%20")
        loc = location.replace(" ", "%20")
        url = (
            f"https://www.naukri.com/jobapi/v3/search?"
            f"noOfResults=20&urlType=search_by_keyword&searchType=adv"
            f"&keyword={kw}&location={loc}&experience=0"
            f"&jobAge=7&src=jobsearchDesk&latLong="
        )
        r    = requests.get(url, headers={**HEADERS, "appid": "109", "systemid": "109"}, timeout=10)
        data = r.json()
        for j in data.get("jobDetails", []):
            title   = j.get("title", "").strip()
            company = j.get("companyName", "").strip()
            loc_str = location
            jurl    = f"https://www.naukri.com{j.get('jdURL', '')}"
            posted  = j.get("footerPlaceholderLabel", "")

            # Use all available description fields
            desc_parts = [
                j.get("jobDesc", ""),
                j.get("jobHighlight", ""),
                " ".join(j.get("tagsAndHighlights", {}).get("highlights", [])),
                j.get("experienceText", ""),
                j.get("educationText", ""),
            ]
            desc = " ".join(str(p) for p in desc_parts if p)

            if not title or not jurl:
                continue
            if not _has_location(loc_str):
                continue
            if not _is_fresher_desc(desc):
                continue

            jobs.append({
                "id":       job_id(jurl, title, company),
                "title":    title,
                "company":  company,
                "location": loc_str,
                "url":      jurl,
                "posted":   posted,
                "source":   "Naukri",
                "fetched_at": datetime.now().isoformat(),
            })
    except Exception as e:
        print(f"  [Naukri] Error ({keyword}/{location}): {e}")
    return jobs


# ── INDEED INDIA (RSS) ────────────────────────────────────────────
def scrape_indeed(keyword, location):
    jobs = []
    try:
        kw  = keyword.replace(" ", "+")
        loc = location.replace(" ", "+")
        url = f"https://in.indeed.com/rss?q={kw}&l={loc}&sort=date&fromage=7"
        r   = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.content, "xml")
        for item in soup.find_all("item")[:15]:
            title   = item.find("title").get_text(strip=True) if item.find("title") else ""
            link    = item.find("link").get_text(strip=True) if item.find("link") else ""
            company_tag = item.find("source")
            company = company_tag.get_text(strip=True) if company_tag else "Unknown"
            pub_date = item.find("pubDate")
            posted  = pub_date.get_text(strip=True) if pub_date else ""
            desc_tag = item.find("description")
            desc    = desc_tag.get_text(separator=" ", strip=True) if desc_tag else ""

            if not title or not link:
                continue
            if not _has_location(location):
                continue
            if not _is_fresher_desc(desc):
                continue

            jobs.append({
                "id":       job_id(link, title, company),
                "title":    title,
                "company":  company,
                "location": location,
                "url":      link,
                "posted":   posted,
                "source":   "Indeed",
                "fetched_at": datetime.now().isoformat(),
            })
    except Exception as e:
        print(f"  [Indeed] Error ({keyword}/{location}): {e}")
    return jobs


# ── MAIN SCRAPE FUNCTION ──────────────────────────────────────────
def fetch_all_jobs():
    """
    Fetch fresher jobs for B.Tech/BE holders.
    Job ROLE can be anything — filter by description only.
    Keywords cover all B.Tech groups: CSE, ECE, EEE, IT, Mech, Civil, any engineering.
    """
    all_jobs  = []
    seen_urls = set()

    print("Fetching B.Tech fresher jobs from LinkedIn, Naukri, Indeed...")

    # B.Tech group keywords — covers all branches and common roles
    search_keywords = [
        # Core B.Tech / BE
        "B.Tech fresher Hyderabad",
        "BE fresher Hyderabad",
        "engineering fresher Hyderabad",
        "any engineering fresher Hyderabad",
        # Branch-specific
        "CSE fresher Hyderabad",
        "ECE fresher Hyderabad",
        "EEE fresher Hyderabad",
        "IT fresher Hyderabad",
        "mechanical engineer fresher Hyderabad",
        "civil engineer fresher Hyderabad",
        # Common B.Tech job roles (job role can be anything)
        "software engineer fresher Hyderabad",
        "software developer fresher Hyderabad",
        "junior developer fresher Hyderabad",
        "python developer fresher Hyderabad",
        "java developer fresher Hyderabad",
        "full stack developer fresher Hyderabad",
        "frontend developer fresher Hyderabad",
        "backend developer fresher Hyderabad",
        "data analyst fresher Hyderabad",
        "network engineer fresher Hyderabad",
        "embedded engineer fresher Hyderabad",
        "VLSI engineer fresher Hyderabad",
        "testing engineer fresher Hyderabad",
        "QA engineer fresher Hyderabad",
        "automation engineer fresher Hyderabad",
        "DevOps fresher Hyderabad",
        "cloud fresher Hyderabad",
        # General
        "graduate engineer trainee Hyderabad",
        "GET Hyderabad",
        "trainee engineer Hyderabad",
        "campus hire Hyderabad",
    ]

    for keyword in search_keywords:
        for location in ["Hyderabad"]:
            try:
                results = scrape_linkedin(keyword, location)
                for job in results:
                    u = job.get("url", "")
                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        all_jobs.append(job)
                delay()

                results = scrape_naukri(keyword, location)
                for job in results:
                    u = job.get("url", "")
                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        all_jobs.append(job)
                delay()

                results = scrape_indeed(keyword, location)
                for job in results:
                    u = job.get("url", "")
                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        all_jobs.append(job)
                delay()

            except Exception as e:
                print(f"  Error fetching {keyword}/{location}: {e}")

    # Deduplicate by job id
    seen_ids    = set()
    unique_jobs = []
    for job in all_jobs:
        if job["id"] not in seen_ids:
            seen_ids.add(job["id"])
            unique_jobs.append(job)

    # Sort newest first
    unique_jobs.sort(key=lambda x: x.get("posted", ""), reverse=True)

    print(f"Found {len(unique_jobs)} B.Tech fresher jobs")
    return unique_jobs
