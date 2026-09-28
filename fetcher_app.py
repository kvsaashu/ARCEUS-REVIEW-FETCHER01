import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from google_play_scraper import reviews, Sort, app as play_app
from matcher import match_keywords, match_member_name, highlight_matches, match_ending_hint
from config import DEFAULT_COUNTRY, DEFAULT_LANG, MAX_FETCH_SCAN

def extract_package_id(raw_input: str) -> str:
    """Extracts package id if user pasted a full Play Store URL or raw ID."""
    raw = raw_input.strip()
    if "play.google.com" in raw:
        m = re.search(r'id=([a-zA-Z0-9._]+)', raw)
        if m:
            return m.group(1)
    # Remove any extra query parameters or spaces
    return raw.split("&")[0].split("?")[0].strip()

def get_app_info(package_id: str) -> Dict[str, Any]:
    """Retrieves app metadata from Google Play."""
    try:
        info = play_app(package_id, lang=DEFAULT_LANG, country=DEFAULT_COUNTRY)
        return {
            "title": info.get("title", package_id),
            "icon": info.get("icon", ""),
            "developer": info.get("developer", ""),
            "installs": info.get("installs", ""),
            "score": round(float(info.get("score") or 0), 1),
            "url": info.get("url", f"https://play.google.com/store/apps/details?id={package_id}")
        }
    except Exception as e:
        print(f"Error fetching app info for {package_id}: {e}")
        return {
            "title": package_id,
            "icon": "",
            "developer": "",
            "installs": "",
            "score": 0.0,
            "url": f"https://play.google.com/store/apps/details?id={package_id}"
        }

def format_review_date(at_val) -> tuple:
    """Returns (date_str 'YYYY-MM-DD', time_str 'HH:MM:SS')."""
    if hasattr(at_val, "strftime"):
        return at_val.strftime("%Y-%m-%d"), at_val.strftime("%H:%M:%S")
    s = str(at_val)
    return s[:10], s[11:19]

def fetch_app_reviews(
    package_id: str,
    search_date: Optional[str] = None,
    rating: Optional[int] = None,
    keyword_text: Optional[str] = None,
    exact_word: bool = False,
    members_text: Optional[str] = None,
    ending_hint: Optional[str] = None,
    max_scan: int = MAX_FETCH_SCAN
) -> Dict[str, Any]:
    """
    Fetches and filters Google Play reviews for a specific app package.
    """
    package = extract_package_id(package_id)
    
    matched_reviews = []
    seen_review_ids = set()
    total_scanned = 0
    search_date = search_date.strip() if search_date else ""

    # In India, users post in both English (en) and Hindi (hi). Fetch both to catch all reviews.
    languages = [DEFAULT_LANG]
    if DEFAULT_COUNTRY == "in" and "hi" not in languages:
        languages.append("hi")

    from concurrent.futures import ThreadPoolExecutor

    def fetch_lang_batch(lang: str):
        token = None
        lang_items = []
        limit = max_scan // len(languages)
        scanned_count = 0
        while scanned_count < limit:
            try:
                batch, token = reviews(
                    package,
                    lang=lang,
                    country=DEFAULT_COUNTRY,
                    sort=Sort.NEWEST,
                    count=200,
                    continuation_token=token
                )
            except Exception as e:
                print(f"Play Store review fetch error ({lang}): {e}")
                break

            if not batch:
                break

            lang_items.extend(batch)
            scanned_count += len(batch)

            if search_date:
                oldest_date, _ = format_review_date(batch[-1].get("at"))
                if oldest_date < search_date:
                    break

            if not token:
                break
        return lang_items

    # Fetch app metadata and all language batches simultaneously in parallel
    with ThreadPoolExecutor(max_workers=len(languages) + 1) as executor:
        info_future = executor.submit(get_app_info, package)
        lang_futures = [executor.submit(fetch_lang_batch, lang) for lang in languages]
        
        app_info = info_future.result()
        results = [f.result() for f in lang_futures]

    all_raw_batches = []
    for b in results:
        all_raw_batches.extend(b)

    for r in all_raw_batches:
        rev_id = str(r.get("reviewId") or "")
        if rev_id and rev_id in seen_review_ids:
            continue
        if rev_id:
            seen_review_ids.add(rev_id)

        total_scanned += 1
        r_date, r_time = format_review_date(r.get("at"))

        # Date filter
        if search_date and r_date != search_date:
            continue

                # Rating filter
        score = int(r.get("score") or 0)
        if rating and score != int(rating):
            continue

        content = str(r.get("content") or "")
        user_name = str(r.get("userName") or "Anonymous")

        # Keyword / Comment match (App Mode strictly requires exact comment match)
        is_matched, matched_kws = match_keywords(content, keyword_text or "", exact_word=exact_word, is_app_mode=True)
        if not is_matched:
            continue

        # Ending / Trailing Hint filter (jo last mai hote hain)
        if ending_hint and ending_hint.strip():
            if not match_ending_hint(content, ending_hint):
                continue
            if ending_hint.strip() not in matched_kws:
                matched_kws.append(ending_hint.strip())

        # Member name filter
        if members_text and members_text.strip():
            if not match_member_name(user_name, members_text):
                continue

        # Review item
        matched_reviews.append({
            "service_type": "APP",
            "target_id": package,
            "target_name": app_info["title"],
            "review_id": str(r.get("reviewId") or f"{package}_{user_name}_{r_date}_{r_time}"),
            "user_name": user_name,
            "user_image": str(r.get("userImage") or ""),
            "rating": score,
            "review_text": content,
            "highlighted_text": highlight_matches(content, matched_kws),
            "review_date": r_date,
            "review_time": r_time,
            "matched_keywords": ", ".join(matched_kws) if matched_kws else "Matched",
            "thumbs_up": r.get("thumbsUpCount", 0)
        })

    return {
        "success": True,
        "app_info": app_info,
        "total_scanned": total_scanned,
        "total_matched": len(matched_reviews),
        "reviews": matched_reviews
    }

