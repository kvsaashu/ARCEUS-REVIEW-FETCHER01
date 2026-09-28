import re
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from matcher import match_keywords, match_member_name, highlight_matches, match_ending_hint
from database import get_setting

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def parse_relative_date(date_str: str) -> str:
    """
    Parses Google Maps relative date strings like '3 days ago', 'a month ago', 'yesterday'
    into an ISO date string (YYYY-MM-DD).
    """
    now = datetime.now()
    if not date_str:
        return now.strftime("%Y-%m-%d")
    s = date_str.lower().strip()
    m_hr = re.search(r'(\d+)\s+hour', s)
    if m_hr:
        return (now - timedelta(hours=int(m_hr.group(1)))).strftime("%Y-%m-%d")
    if "an hour ago" in s:
        return (now - timedelta(hours=1)).strftime("%Y-%m-%d")
    if any(w in s for w in ["minute", "second", "moment", "today", "now", "just"]):
        return now.strftime("%Y-%m-%d")
    if "yesterday" in s:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    m_day = re.search(r'(\d+)\s+day', s)
    if m_day:
        return (now - timedelta(days=int(m_day.group(1)))).strftime("%Y-%m-%d")
    if "a day ago" in s or "an day ago" in s:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    m_wk = re.search(r'(\d+)\s+week', s)
    if m_wk:
        return (now - timedelta(days=int(m_wk.group(1)) * 7)).strftime("%Y-%m-%d")
    if "a week ago" in s:
        return (now - timedelta(days=7)).strftime("%Y-%m-%d")

    m_mo = re.search(r'(\d+)\s+month', s)
    if m_mo:
        return (now - timedelta(days=int(m_mo.group(1)) * 30)).strftime("%Y-%m-%d")
    if "a month ago" in s:
        return (now - timedelta(days=30)).strftime("%Y-%m-%d")

    m_yr = re.search(r'(\d+)\s+year', s)
    if m_yr:
        return (now - timedelta(days=int(m_yr.group(1)) * 365)).strftime("%Y-%m-%d")
    if "a year ago" in s:
        return (now - timedelta(days=365)).strftime("%Y-%m-%d")

    return now.strftime("%Y-%m-%d")

def normalize_map_relative_time(s: str) -> tuple:
    """
    Normalizes relative time strings into a (unit, count) tuple:
    - ('hour', N) (where 0 is just now / minutes / today)
    - ('day', N) (1 for yesterday / a day ago)
    - ('week', N) (1 for a week ago)
    - ('month', N) (1 for a month ago)
    - ('year', N) (1 for a year ago)
    """
    if not s:
        return ("unknown", 0)
    s = s.lower().strip()
    if any(w in s for w in ["minute", "second", "moment", "now", "just", "today"]):
        return ("hour", 0)
    m_hr = re.search(r'(\d+)\s+hour', s)
    if m_hr:
        return ("hour", int(m_hr.group(1)))
    if "an hour" in s or "1 hour" in s or "hour" in s:
        return ("hour", 1)

    if "yesterday" in s or "a day" in s or "an day" in s:
        return ("day", 1)
    m_day = re.search(r'(\d+)\s+day', s)
    if m_day:
        return ("day", int(m_day.group(1)))

    if "a week" in s:
        return ("week", 1)
    m_wk = re.search(r'(\d+)\s+week', s)
    if m_wk:
        return ("week", int(m_wk.group(1)))

    if "a month" in s:
        return ("month", 1)
    m_mo = re.search(r'(\d+)\s+month', s)
    if m_mo:
        return ("month", int(m_mo.group(1)))

    if "a year" in s:
        return ("year", 1)
    m_yr = re.search(r'(\d+)\s+year', s)
    if m_yr:
        return ("year", int(m_yr.group(1)))

    return ("unknown", 0)

def match_map_date_filter(date_str: str, filter_val: Optional[str]) -> bool:
    """
    Matches Google Maps relative date strings (e.g. '3 hours ago', '4 days ago', 'a month ago', '2 months ago')
    against user-specified relative time or ISO date.
    """
    if not filter_val or filter_val.strip().upper() in ["ALL", "ANY", "ALL TIME", ""]:
        return True

    if not date_str:
        return True

    raw_lower = date_str.lower().strip()
    f_lower = filter_val.lower().strip()

    # 1. Direct textual match or substring
    if f_lower in raw_lower or raw_lower in f_lower:
        return True

    r_unit, r_count = normalize_map_relative_time(raw_lower)

    # 2. Hours / Minutes / Today / Just now
    if any(k in f_lower for k in ["hour", "today", "now", "minute", "moment", "recent", "24h"]):
        return r_unit == "hour" or (r_unit == "day" and r_count <= 1)

    # 3. 1-3 Days ago (Yesterday - 3 Days)
    if "1-3" in f_lower or "few days" in f_lower:
        return r_unit == "day" and 1 <= r_count <= 3

    # 4. 4 Days ago (exact 4 days with +-1 tolerance: 3 to 5 days)
    if "4 day" in f_lower:
        return r_unit == "day" and 3 <= r_count <= 5

    # 5. 5-7 Days ago / 4-7 Days ago
    if "5-7" in f_lower or "4-7" in f_lower:
        return (r_unit == "day" and 4 <= r_count <= 7) or (r_unit == "week" and r_count == 1)

    # 6. Weeks matching (e.g. "1 week ago", "2 weeks ago", "3 weeks ago")
    if "week" in f_lower:
        f_unit, f_count = normalize_map_relative_time(f_lower)
        target_wk = f_count if f_unit == "week" else 1
        if r_unit == "week":
            return r_count == target_wk
        if r_unit == "day":
            approx_wk = round(r_count / 7)
            return approx_wk == target_wk
        return False

    # 7. Months matching (e.g. "a month ago", "2 months ago", "3 months ago", "6 months ago")
    if "month" in f_lower:
        f_unit, f_count = normalize_map_relative_time(f_lower)
        target_mo = f_count if f_unit == "month" else 1
        if "3+" in f_lower:
            return (r_unit == "month" and r_count >= 3) or (r_unit == "year")
        if "6" in f_lower:
            return (r_unit == "month" and 5 <= r_count <= 7)
        if r_unit == "month":
            return r_count == target_mo
        if r_unit == "week" and target_mo == 1:
            return r_count >= 4  # 4 weeks is ~ 1 month
        return False

    # 8. Years matching
    if "year" in f_lower:
        return r_unit == "year"

    # 9. ISO Date string fallback check (YYYY-MM-DD) with +-2 days tolerance
    if re.match(r'^\d{4}-\d{2}-\d{2}$', filter_val.strip()):
        try:
            target_dt = datetime.strptime(filter_val.strip(), "%Y-%m-%d")
            approx_date = parse_relative_date(date_str)
            approx_dt = datetime.strptime(approx_date, "%Y-%m-%d")
            return abs((approx_dt - target_dt).days) <= 2
        except:
            pass

    return False

def resolve_maps_url(target_input: str) -> Dict[str, str]:
    """
    Expands shortened Google Maps URLs (e.g. maps.app.goo.gl) and extracts place info.
    """
    target = target_input.strip()
    full_url = target

    if "goo.gl" in target or "maps.app.goo.gl" in target:
        try:
            resp = requests.head(target, allow_redirects=True, headers=HEADERS, timeout=10)
            full_url = resp.url
        except Exception as e:
            print(f"Error resolving Maps short URL: {e}")

    # Remove entry=tts which forces accessibility limited mode
    clean_url = full_url.replace("entry=tts&", "").replace("entry=tts", "")

    # Extract place title from URL path e.g. /place/Store+Name/
    title = ""
    m = re.search(r'/place/([^/@]+)', clean_url)
    if m:
        title = m.group(1)

    # Extract coordinates
    m_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', clean_url)
    lat, lng = m_coords.groups() if m_coords else ("0", "0")

    # Extract hex place ID
    m_hex = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', clean_url)
    hex_id = m_hex.group(1) if m_hex else ""

    # Extract feature ID
    m_feat = re.search(r'(!16s[^!&?]+)', clean_url)
    feat = m_feat.group(1) if m_feat else ""

    cid = ""
    m_cid = re.search(r'0x[0-9a-fA-F]+:(0x[0-9a-fA-F]+)', clean_url)
    if m_cid:
        cid = m_cid.group(1)

    # If place coordinates and hex ID are present, construct direct 17z reviews URL
    if hex_id and lat != "0" and title:
        direct_url = f"https://www.google.com/maps/place/{title}/@{lat},{lng},17z/data=!4m8!3m7!1s{hex_id}!8m2!3d{lat}!4d{lng}!9m1!1b1{feat}"
    elif "!9m1!1b1" in clean_url:
        direct_url = clean_url
    else:
        direct_url = clean_url

    display_title = title.replace("+", " ") if title else target_input
    return {
        "title": display_title,
        "full_url": direct_url,
        "cid": cid
    }

def scrape_maps_reviews_selenium(
    target_input: str,
    search_date: Optional[str] = None,
    rating: Optional[int] = None,
    keyword_text: Optional[str] = None,
    exact_word: bool = False,
    members_text: Optional[str] = None,
    ending_hint: Optional[str] = None,
    max_scrolls: int = 8
) -> Dict[str, Any]:
    """
    Scrapes Google Maps reviews directly using headless Chrome (zero API key required).
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By

    info = resolve_maps_url(target_input)
    clean_url = info["full_url"]
    place_title = info["title"]

    options = Options()
    options.page_load_strategy = "eager"
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-default-apps")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2
    })
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    driver = None
    matched_reviews = []
    total_scanned = 0

    try:
        driver = webdriver.Chrome(options=options)
        print(f"Loading URL: {clean_url[:80]}...", flush=True)
        driver.get(clean_url)

        # Extract place title from H1 if present
        try:
            h1 = driver.find_elements(By.TAG_NAME, "h1")
            if h1 and h1[0].text.strip():
                place_title = h1[0].text.strip()
        except:
            pass

        def dismiss_modal():
            try:
                btns = driver.find_elements(By.XPATH, '//button[contains(., "Dismiss")]')
                if btns:
                    btns[0].click()
                    return True
            except:
                pass
            return False

        sort_btn = None
        for _ in range(16):
            dismiss_modal()
            btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Sort") or contains(., "Sort")]')
            if btns:
                sort_btn = btns[0]
                break
            time.sleep(0.15)

        sorted_by_newest = False
        print(f"Sort button found: {bool(sort_btn)}", flush=True)
        if sort_btn:
            from selenium.webdriver.common.action_chains import ActionChains
            try:
                ActionChains(driver).move_to_element(sort_btn).pause(0.05).click().perform()
            except Exception as e:
                try:
                    driver.execute_script("arguments[0].click();", sort_btn)
                except:
                    pass

            items = []
            for attempt in range(12):
                dismiss_modal()
                items = driver.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
                if len(items) >= 2:
                    break
                if attempt in [1, 4]:
                    try:
                        driver.execute_script("arguments[0].click();", sort_btn)
                    except:
                        pass
                time.sleep(0.15)

            print(f"Menu items found: {len(items)}", flush=True)
            newest_btn = None
            if len(items) >= 2:
                newest_btn = items[1]
            else:
                alt = driver.find_elements(By.XPATH, '//*[contains(text(), "Newest") or contains(text(), "नवीनतम") or contains(@data-index, "1")]')
                if alt:
                    newest_btn = alt[0]

            if newest_btn:
                try:
                    newest_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", newest_btn)
                print("Clicked Newest successfully!", flush=True)
                sorted_by_newest = True

        # Quick poll for cards to render after sort (checks every 150ms)
        cards = []
        for p in range(25):
            cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
            if cards:
                print(f"Cards loaded at poll {p+1} ({p*0.15+0.15:.2f}s): {len(cards)}", flush=True)
                break
            time.sleep(0.15)
        
        if not cards:
            print("WARNING: 0 cards found after sort, saving debug screenshot...", flush=True)
            try:
                driver.save_screenshot("debug_map_empty_cards.png")
            except:
                pass

        target_dt = None
        if search_date:
            try:
                target_dt = datetime.strptime(search_date, "%Y-%m-%d")
            except:
                pass

        if cards:
            effective_scrolls = min(max_scrolls, 4)
            for s in range(effective_scrolls):
                last_card = cards[-1]
                # If sorted by newest and searching by date, check if oldest card exceeds date window
                if sorted_by_newest and target_dt:
                    try:
                        d_str = last_card.find_element(By.CSS_SELECTOR, "span.rsqaWe").text.strip()
                        oldest_date = parse_relative_date(d_str)
                        oldest_dt = datetime.strptime(oldest_date, "%Y-%m-%d")
                        if (target_dt - oldest_dt).days > 2:
                            print(f"Oldest review date {oldest_date} is older than target {search_date}. Early stopping scroll at scroll {s}.", flush=True)
                            break
                    except:
                        pass

                driver.execute_script("arguments[0].scrollIntoView(true);", last_card)
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                    "type": "mouseWheel",
                    "x": 250,
                    "y": 700,
                    "deltaX": 0,
                    "deltaY": 1200
                })
                time.sleep(0.35)
                new_cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
                if len(new_cards) == len(cards):
                    break
                cards = new_cards
                if len(cards) >= 40:
                    break

        # Step 5: Turbo In-Browser Batch Extraction (Single JS execution extracts all cards in ~10ms)
        js_extract_code = """
        const cards = Array.from(document.querySelectorAll('div.jftiEf'));
        cards.forEach(c => {
            const moreBtn = c.querySelector('button.w8nwRe, button[aria-label*="more" i], button[aria-label*="ज़्यादा" i]');
            if (moreBtn) {
                try { moreBtn.click(); } catch(e) {}
            }
        });
        return cards.map(c => {
            const authorEl = c.querySelector('div.d4r55');
            const contentEl = c.querySelector('span.wiI7pd');
            const starsEl = c.querySelector('span.kvMYJc');
            const dateEl = c.querySelector('span.rsqaWe');
            return {
                author: authorEl ? authorEl.innerText.trim() : 'Anonymous',
                content: contentEl ? contentEl.innerText.trim() : '',
                aria_stars: starsEl ? (starsEl.getAttribute('aria-label') || '') : '',
                date_str: dateEl ? dateEl.innerText.trim() : ''
            };
        });
        """
        raw_card_data = driver.execute_script(js_extract_code) or []
        print(f"Total cards extracted in-browser: {len(raw_card_data)}", flush=True)

        seen_authors = set()
        for idx, item in enumerate(raw_card_data):
            total_scanned += 1
            author = item.get("author") or "Anonymous"
            if author in seen_authors:
                continue
            seen_authors.add(author)

            content = item.get("content") or ""
            aria = item.get("aria_stars") or ""
            m = re.search(r'(\d+)', aria)
            score = int(m.group(1)) if m else 5
            date_str = item.get("date_str") or ""
            r_date = parse_relative_date(date_str)
            u_clean = author.encode('ascii', 'replace').decode()
            txt_clean = content.encode('ascii', 'replace').decode()
            print(f"Card #{idx+1}: {u_clean} | Score: {score} | Date: {r_date} ({date_str}) | Text: {txt_clean[:40]}", flush=True)

            # Date filter (handles relative phrases like '3 hours ago', '4 days ago', 'a month ago', '2 months ago', or 'ALL')
            if search_date and search_date.strip():
                if not match_map_date_filter(date_str, search_date):
                    continue

            # Rating filter
            if rating and score != int(rating):
                continue

            # Keyword / Comment match (uses 70% threshold and smart typo engine)
            is_matched, matched_kws = match_keywords(content, keyword_text or "", exact_word=exact_word)
            if not is_matched:
                continue

            # Ending hint filter
            if ending_hint and ending_hint.strip():
                if not match_ending_hint(content, ending_hint):
                    continue
                if ending_hint.strip() not in matched_kws:
                    matched_kws.append(ending_hint.strip())

            # Member name filter
            if members_text and members_text.strip():
                if not match_member_name(author, members_text):
                    continue

            matched_reviews.append({
                "service_type": "MAP",
                "target_id": target_input,
                "target_name": place_title,
                "review_id": f"map_{author}_{r_date}",
                "user_name": author,
                "user_image": "https://lh3.googleusercontent.com/a/default-user",
                "rating": score,
                "review_text": content,
                "highlighted_text": highlight_matches(content, matched_kws),
                "review_date": date_str if date_str else r_date,
                "raw_date": date_str,
                "approx_date": r_date,
                "review_time": date_str if date_str else "12:00:00",
                "matched_keywords": ", ".join(matched_kws) if matched_kws else "70% Comment Match"
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Selenium Maps scraping error: {e}", flush=True)
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    return {
        "success": True,
        "place_info": {
            "title": place_title,
            "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/generic_business-71.png",
            "score": 4.9,
            "url": clean_url
        },
        "total_scanned": total_scanned,
        "total_matched": len(matched_reviews),
        "reviews": matched_reviews
    }

def fetch_map_reviews_via_places_api(
    place_id: str,
    api_key: str,
    search_date: Optional[str] = None,
    rating: Optional[int] = None,
    keyword_text: Optional[str] = None,
    exact_word: bool = False,
    members_text: Optional[str] = None,
    ending_hint: Optional[str] = None
) -> Dict[str, Any]:
    """Fetches reviews using official Google Places Details API if API key is provided."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,rating,reviews,user_ratings_total,icon",
        "key": api_key,
        "reviews_sort": "newest"
    }

    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    result = data.get("result", {})
    raw_reviews = result.get("reviews", [])

    matched_reviews = []
    for r in raw_reviews:
        t_val = r.get("time", 0)
        dt = datetime.fromtimestamp(t_val) if t_val else datetime.now()
        r_date = dt.strftime("%Y-%m-%d")
        r_time = dt.strftime("%H:%M:%S")

        if search_date and r_date != search_date:
            continue

        score = int(r.get("rating", 0))
        if rating and score != int(rating):
            continue

        author = str(r.get("author_name", "Anonymous"))
        content = str(r.get("text", ""))

        is_matched, matched_kws = match_keywords(content, keyword_text or "", exact_word=exact_word)
        if not is_matched:
            continue

        if ending_hint and ending_hint.strip():
            if not match_ending_hint(content, ending_hint):
                continue
            if ending_hint.strip() not in matched_kws:
                matched_kws.append(ending_hint.strip())

        if members_text and not match_member_name(author, members_text):
            continue

        matched_reviews.append({
            "service_type": "MAP",
            "target_id": place_id,
            "target_name": result.get("name", place_id),
            "review_id": f"map_{place_id}_{author}_{t_val}",
            "user_name": author,
            "user_image": r.get("profile_photo_url", ""),
            "rating": score,
            "review_text": content,
            "highlighted_text": highlight_matches(content, matched_kws),
            "review_date": r_date,
            "review_time": r_time,
            "matched_keywords": ", ".join(matched_kws) if matched_kws else "Matched"
        })

    return {
        "success": True,
        "place_info": {
            "title": result.get("name", place_id),
            "icon": result.get("icon", ""),
            "score": result.get("rating", 0.0),
            "total_ratings": result.get("user_ratings_total", 0)
        },
        "total_scanned": len(raw_reviews),
        "total_matched": len(matched_reviews),
        "reviews": matched_reviews
    }

def fetch_map_reviews(
    target_input: str,
    search_date: Optional[str] = None,
    rating: Optional[int] = None,
    keyword_text: Optional[str] = None,
    exact_word: bool = False,
    members_text: Optional[str] = None,
    ending_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for Google Maps Review Fetching.
    Prioritizes Places API if key is provided and target is a Place ID.
    Otherwise uses Headless Chrome Direct Web Fetcher (Zero Key Required).
    """
    places_api_key = get_setting("GOOGLE_PLACES_API_KEY", "")

    # Check if target is directly a Place ID and we have API key
    if places_api_key and (target_input.startswith("ChIJ") or len(target_input) == 27):
        try:
            return fetch_map_reviews_via_places_api(
                target_input, places_api_key, search_date, rating, keyword_text, exact_word, members_text, ending_hint
            )
        except Exception as e:
            print(f"Places API error: {e}")

    # Headless Browser Scraper (free, zero API key required)
    return scrape_maps_reviews_selenium(
        target_input=target_input,
        search_date=search_date,
        rating=rating,
        keyword_text=keyword_text,
        exact_word=exact_word,
        members_text=members_text,
        ending_hint=ending_hint
    )
