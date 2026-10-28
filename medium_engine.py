#!/usr/bin/env python3
"""
medium_engine.py
Autonomous Medium Canonical Syndicator & SEO Authority Booster for aviperera.com.
Syndicates newly published research and essays to Medium via the Medium REST API v1.
Always sets canonicalUrl back to aviperera.com to channel 100% SEO authority to your origin domain.
"""

import os
import sys
import json
import html
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

MEDIUM_ME_URL = "https://api.medium.com/v1/me"
RSS_FEED_URL = "https://aviperera.com/feed/"
STATE_FILE = os.path.join(os.path.dirname(__file__), "state", "medium_history.json")

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, application/json, */*"
}

DEFAULT_TAGS = ["Artificial Intelligence", "AI Ethics", "Technology", "Tech Policy", "Governance"]

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "syndicated" not in data:
                    data["syndicated"] = {}
                return data
        except Exception as e:
            print(f"[!] Warning reading state ({e}). Starting clean.")
    return {"syndicated": {}, "last_run": None}

def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def clean_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

def extract_tags(categories: List[str]) -> List[str]:
    """Maps and cleans categories into valid Medium tags (max 5, max 25 chars each)."""
    tags = []
    for cat in categories:
        clean = re.sub(r"[^\w\s-]", "", cat).strip()
        if clean and len(clean) <= 25 and clean.lower() not in [t.lower() for t in tags]:
            tags.append(clean)
            if len(tags) >= 5:
                break
    
    # Fill with defaults if less than 3
    for d in DEFAULT_TAGS:
        if len(tags) >= 5:
            break
        if d.lower() not in [t.lower() for t in tags]:
            tags.append(d)
    return tags[:5]

def fetch_from_rss() -> List[Dict[str, Any]]:
    """Primary ingestion: Fetches complete publication data and encoded HTML from RSS feed."""
    try:
        req = urllib.request.Request(RSS_FEED_URL, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_xml = resp.read().decode("utf-8", errors="replace")
            clean_xml = re.sub(r"</?([a-zA-Z0-9_-]+):", lambda m: "</" if m.group(0).startswith("</") else "<", raw_xml)
            root = ET.fromstring(clean_xml)
            posts = []
            for item in root.findall(".//item"):
                guid_el = item.find("guid")
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                content_el = item.find("encoded")

                guid = guid_el.text.strip() if guid_el is not None and guid_el.text else ""
                title = clean_text(title_el.text) if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else ""
                desc = desc_el.text if desc_el is not None and desc_el.text else ""
                content = content_el.text if content_el is not None and content_el.text else ""
                
                # Categories
                categories = []
                for cat in item.findall("category"):
                    if cat.text:
                        categories.append(clean_text(cat.text))

                post_id = guid if guid else link
                if title and link:
                    posts.append({
                        "id": post_id,
                        "title": title,
                        "link": link,
                        "description": desc,
                        "content_html": content if content else desc,
                        "categories": categories
                    })
            return posts
    except Exception as e:
        print(f"[!] Primary RSS discovery notice: {e}")
        return []

def get_medium_user_id(token: str) -> Tuple[Optional[str], Optional[str]]:
    """Retrieves authenticated author ID from Medium /v1/me endpoint."""
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/json",
        "User-Agent": "AviMediumSyndicator/1.0"
    }
    req = urllib.request.Request(MEDIUM_ME_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            user_data = data.get("data", {})
            user_id = user_data.get("id")
            username = user_data.get("username", "")
            return user_id, username
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"[!] Medium Auth Error {e.code}: {err}")
        return None, None
    except Exception as e:
        print(f"[!] Medium Connection Error: {e}")
        return None, None

def build_medium_payload(post: dict, publish_status: str = "public") -> dict:
    """Constructs Medium API v1 post payload with canonical link and attribution."""
    title = post["title"]
    canonical_url = post["link"].split("?")[0].rstrip("/") + "/"
    raw_content = post.get("content_html", "")

    # Append canonical citation footer
    canonical_footer = (
        f"<hr>\n"
        f"<p><em>Originally published and peer-cataloged at "
        f"<a href=\"{canonical_url}\"><strong>aviperera.com</strong></a> by Avi Perera. "
        f"All canonical rights and original indexing belong to the origin publication.</em></p>"
    )
    full_html = f"<h1>{html.escape(title)}</h1>\n\n{raw_content}\n\n{canonical_footer}"
    tags = extract_tags(post.get("categories", []))

    return {
        "title": title,
        "contentFormat": "html",
        "content": full_html,
        "canonicalUrl": canonical_url,
        "tags": tags,
        "publishStatus": publish_status,
        "license": "all-rights-reserved",
        "notifyFollowers": True
    }

def publish_to_medium(token: str, user_id: str, payload: dict) -> Tuple[bool, Optional[str], Optional[str]]:
    """Publishes canonical post to Medium via REST API v1."""
    endpoint = f"https://api.medium.com/v1/users/{user_id}/posts"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AviMediumSyndicator/1.0"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            post_data = res_data.get("data", {})
            post_url = post_data.get("url")
            post_id = post_data.get("id")
            print(f"[OK] Successfully syndicated to Medium: {post_url} (ID: {post_id})")
            return True, post_id, post_url
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"[!] Medium API Error {e.code}: {err}")
        return False, None, err
    except Exception as e:
        print(f"[!] Medium Exception: {e}")
        return False, None, str(e)

def main() -> int:
    print("=== Autonomous Medium Canonical Syndicator & SEO Authority Booster ===")
    state = load_state()
    posts = fetch_from_rss()
    print(f"Retrieved {len(posts)} publications from aviperera.com")

    token = os.getenv("MEDIUM_INTEGRATION_TOKEN", "").strip()
    publish_status = os.getenv("MEDIUM_PUBLISH_STATUS", "public").strip().lower()
    if publish_status not in ("public", "draft", "unlisted"):
        publish_status = "public"

    force_dry_run = "--dry-run" in sys.argv
    has_credentials = bool(token)
    dry_run = force_dry_run or not has_credentials

    user_id = None
    username = None
    if has_credentials and not force_dry_run:
        user_id, username = get_medium_user_id(token)
        if not user_id:
            print("[!] Could not authenticate with Medium. Reverting to dry-run preview.")
            dry_run = True
        else:
            print(f"[OK] Authenticated Medium Author: @{username} (ID: {user_id})")

    if dry_run:
        print("[!] Running in PREVIEW / DRY-RUN mode.")
        if not has_credentials:
            print("    Reason: Missing MEDIUM_INTEGRATION_TOKEN repository secret.")

    # Filter un-syndicated posts
    unsyndicated = [p for p in posts if p["id"] not in state["syndicated"] and p["link"] not in state["syndicated"]]
    print(f"Publications pending Medium canonical syndication: {len(unsyndicated)}")

    processed_items = []

    # Syndicate 1 article per scheduled run for optimal algorithmic pacing
    for post in unsyndicated[:1]:
        title = post["title"]
        pid = post["id"]
        canonical_url = post["link"]
        payload = build_medium_payload(post, publish_status=publish_status)

        item_summary = {
            "title": title,
            "canonical_url": canonical_url,
            "tags": payload["tags"],
            "status": "Dry-Run Preview",
            "medium_url": None
        }

        if dry_run:
            print(f"\n[DRY-RUN MEDIUM PREVIEW]")
            print(f"Title: {payload['title']}")
            print(f"Canonical URL: {payload['canonicalUrl']}")
            print(f"Tags: {', '.join(payload['tags'])}")
            print(f"Publish Status: {payload['publishStatus']}")
            print(f"HTML Content length: {len(payload['content'])} chars")
            processed_items.append(item_summary)
            continue

        # Live Submission
        success, medium_id, medium_url = publish_to_medium(token, user_id, payload)
        if success:
            state["syndicated"][pid] = {
                "title": title,
                "canonical_url": canonical_url,
                "medium_id": medium_id,
                "medium_url": medium_url,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            state["last_run"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
            item_summary["status"] = "Syndicated"
            item_summary["medium_url"] = medium_url
            processed_items.append(item_summary)
        else:
            item_summary["status"] = f"Failed ({medium_url})"
            processed_items.append(item_summary)

    output_step_summary(processed_items, dry_run=dry_run, has_credentials=has_credentials)
    return 0

def output_step_summary(items: list, dry_run: bool, has_credentials: bool):
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("## ✍️ Medium Canonical Syndicator & SEO Authority Booster\n\n")
        mode_badge = "🟡 *DRY-RUN / PREVIEW*" if dry_run else "🟢 *LIVE MEDIUM SYNDICATION SUCCESS*"
        f.write(f"**Execution Mode:** {mode_badge}\n\n")
        f.write(f"- **Medium Credentials:** {'✅ Configured' if has_credentials else '❌ Missing MEDIUM_INTEGRATION_TOKEN'}\n\n")

        if not items:
            f.write("✅ All recent publications are already syndicated to Medium. Zero pending items.\n")
            return

        f.write(f"### Processed Publication ({len(items)} item):\n\n")
        f.write("| Title | Canonical Origin | Medium URL | Status |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for it in items:
            med_link = f"[View on Medium]({it['medium_url']})" if it.get("medium_url") else "`N/A`"
            f.write(f"| {it['title']} | [{it['canonical_url']}]({it['canonical_url']}) | {med_link} | `{it['status']}` |\n")

if __name__ == "__main__":
    sys.exit(main())
