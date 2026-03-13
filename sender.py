"""
Telegram message sender for B.Tech Jobs Fresher Bot
Formats job info and sends to channel
"""
import requests
import re
import time
from datetime import datetime, timedelta
import config

API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"


def _escape(text):
    """Escape Telegram Markdown v1 special characters."""
    if not text:
        return ""
    for ch in ["_", "*", "`", "["]:
        text = text.replace(ch, f"\\{ch}")
    return text


def _post(text, chat_id=None):
    """Post message to Telegram channel."""
    cid = chat_id or config.CHAT_ID
    if not cid:
        print("[Telegram] CHAT_ID not set.")
        return False
    try:
        r = requests.post(
            f"{API}/sendMessage",
            json={
                "chat_id": cid,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return True

        # Fallback: plain text
        r2 = requests.post(
            f"{API}/sendMessage",
            json={
                "chat_id": cid,
                "text": re.sub(r"[*_`\[\]]", "", text),
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        return r2.status_code == 200

    except Exception as e:
        print(f"[Telegram] Send error: {e}")
        return False


def _format_posted(posted, fetched_at=""):
    """Return human-readable posted time in IST."""
    IST_OFFSET = timedelta(hours=5, minutes=30)

    p = str(posted or "").strip()

    # Try ISO date/datetime format
    if p and re.match(r"\d{4}-\d{2}-\d{2}", p):
        try:
            dt = datetime.fromisoformat(p[:19])
            if len(p) >= 16:
                dt_ist = dt + IST_OFFSET
                return dt_ist.strftime("%d %b %Y, %I:%M %p IST")
            else:
                return dt.strftime("%d %b %Y")
        except Exception:
            pass

    if p:
        return p

    if fetched_at:
        try:
            dt = datetime.fromisoformat(str(fetched_at)[:19])
            dt_ist = dt + IST_OFFSET
            return f"Found at {dt_ist.strftime('%d %b %Y, %I:%M %p IST')}"
        except Exception:
            pass

    return ""


def format_job(job):
    """Format job details for Telegram posting (Markdown)."""
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "Hyderabad")
    url = job.get("url", "")
    source = job.get("source", "")
    posted = job.get("posted", "")

    safe_company = _escape(company)
    safe_title = _escape(title)
    safe_location = _escape(location)
    safe_source = _escape(source)

    lines = [
        f"🔥 *B.Tech Job at {safe_company}*",
        "",
        f"💼 *Role:* {safe_title}",
        f"📍 *Location:* {safe_location}",
    ]

    posted_str = _format_posted(posted, job.get("fetched_at", ""))
    if posted_str:
        lines.append(f"⏰ *Posted:* {_escape(posted_str)}")

    lines += [
        "",
        f"🔗 *Apply:* {url}",
    ]

    if source:
        lines.append(f"📋 _{safe_source}_")

    return "\n".join(lines)


def send_job(job):
    """Send a single job to Telegram channel."""
    msg = format_job(job)
    ok = _post(msg)
    if ok:
        time.sleep(2)
    return ok
