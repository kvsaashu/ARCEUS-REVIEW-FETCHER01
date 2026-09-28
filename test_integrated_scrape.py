import re
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from matcher import match_keywords, match_member_name, highlight_matches, match_ending_hint

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def parse_relative_date(date_str: str) -> str:
    now = datetime.now()
    if not date_str:
        return now.strftime("%Y-%m-%d")
    s = date_str.lower().strip()
    if any(w in s for w in ["hour", "minute", "second", "moment", "today", "now", "just"]):
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

def resolve_maps_url(target_input: str) -> Dict[str, str]:
    target = target_input.strip()
    full_url = target

    if "goo.gl" in target or "maps.app.goo.gl" in target:
        try:
            resp = requests.head(target, allow_redirects=True, headers=HEADERS, timeout=10)
            full_url = resp.url
        except Exception as e:
            print(f"Error resolving Maps short URL: {e}", flush=True)

    clean_url = full_url.replace("entry=tts&", "").replace("entry=tts", "")

    # Extract place components
    title = ""
    m_title = re.search(r'/place/([^/@]+)', clean_url)
    if m_title:
        title = m_title.group(1)

    m_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', clean_url)
    lat, lng = m_coords.groups() if m_coords else ("0", "0")

    m_hex = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', clean_url)
    hex_id = m_hex.group(1) if m_hex else ""

    m_feat = re.search(r'(!16s[^!&?]+)', clean_url)
    feat = m_feat.group(1) if m_feat else ""

    cid = ""
    m_cid = re.search(r'0x[0-9a-fA-F]+:(0x[0-9a-fA-F]+)', clean_url)
    if m_cid:
        cid = m_cid.group(1)

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
    info = resolve_maps_url(target_input)
    clean_url = info["full_url"]
    place_title = info["title"]

    options = Options()
    options.page_load_strategy = "eager"
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    matched_reviews = []
    total_scanned = 0

    def dismiss_modal():
        d_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Dismiss') or contains(@aria-label, 'Dismiss')] | //span[contains(text(), 'Dismiss')]/ancestor::button")
        if d_btns:
            driver.execute_script("arguments[0].click();", d_btns[0])
            time.sleep(0.8)
            return True
        return False

    try:
        print(f"Loading URL: {clean_url[:80]}...", flush=True)
        driver.get(clean_url)
        time.sleep(4)

        # Title from H1 if present
        try:
            h1 = driver.find_elements(By.TAG_NAME, "h1")
            if h1 and h1[0].text.strip():
                place_title = h1[0].text.strip()
        except:
            pass

        dismiss_modal()

        # Step 1: Ensure Reviews view is active
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
        
        if not cards and not sort_btns:
            # Fallback: check tabs or star triggers
            tabs = driver.find_elements(By.CSS_SELECTOR, "button[role='tab']")
            if len(tabs) >= 2:
                driver.execute_script("arguments[0].click();", tabs[1])
                time.sleep(2)
            else:
                stars = driver.find_elements(By.XPATH, "//span[contains(@aria-label, 'stars')]/ancestor::button | //span[contains(@class, 'ceNzKf')]/ancestor::button")
                if stars:
                    driver.execute_script("arguments[0].click();", stars[0])
                    time.sleep(2)
                else:
                    # Scroll panel down to find More reviews
                    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                        "type": "mouseWheel",
                        "x": 250,
                        "y": 600,
                        "deltaX": 0,
                        "deltaY": 1500
                    })
                    time.sleep(1.5)
                    more_btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'More reviews') or contains(., 'More reviews')]")
                    if more_btns:
                        driver.execute_script("arguments[0].click();", more_btns[0])
                        time.sleep(2)

        # Step 2: Sort by Newest (retry up to 4 times with modal handling)
        for attempt in range(4):
            dismiss_modal()
            sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
            if not sort_btns:
                break
            driver.execute_script("arguments[0].click();", sort_btns[0])
            time.sleep(1.2)

            if dismiss_modal():
                continue

            items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
            if items:
                for idx, mi in enumerate(items):
                    txt = mi.text.lower()
                    if "newest" in txt or idx == 1:
                        driver.execute_script("arguments[0].click();", mi)
                        print("Switched sorting to Newest!", flush=True)
                        break
                break

        # Step 3: Wait for cards after sort
        cards = []
        for w in range(12):
            time.sleep(1)
            cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
            if cards:
                print(f"Cards rendered: {len(cards)}", flush=True)
                break

        # Step 4: Scroll to load more cards
        if cards:
            for s in range(max_scrolls):
                last_card = cards[-1]
                driver.execute_script("arguments[0].scrollIntoView(true);", last_card)
                driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                    "type": "mouseWheel",
                    "x": 250,
                    "y": 700,
                    "deltaX": 0,
                    "deltaY": 1200
                })
                time.sleep(1.2)
                new_cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
                if len(new_cards) == len(cards):
                    break
                cards = new_cards
                if len(cards) >= 40:
                    break

        print(f"Total cards ready for processing: {len(cards)}", flush=True)

        # Step 5: Extract and match reviews
        seen_authors = set()
        for idx, c in enumerate(cards):
            total_scanned += 1

            try:
                author = c.find_element(By.CSS_SELECTOR, "div.d4r55").text.strip()
            except:
                author = "Anonymous"

            if author in seen_authors:
                continue
            seen_authors.add(author)

            # Expand truncated text
            try:
                more_btn = c.find_elements(By.CSS_SELECTOR, "button.w8nwRe, button[aria-label*='more' i]")
                if more_btn:
                    driver.execute_script("arguments[0].click();", more_btn[0])
            except:
                pass

            try:
                content = c.find_element(By.CSS_SELECTOR, "span.wiI7pd").text.strip()
            except:
                content = ""

            score = 5
            try:
                stars_el = c.find_element(By.CSS_SELECTOR, "span.kvMYJc")
                aria = stars_el.get_attribute("aria-label") or ""
                m = re.search(r'(\d+)', aria)
                if m:
                    score = int(m.group(1))
            except:
                score = 5

            date_str = ""
            try:
                date_str = c.find_element(By.CSS_SELECTOR, "span.rsqaWe").text.strip()
            except:
                pass
            r_date = parse_relative_date(date_str)

            # Date filter (within 2 days margin)
            if search_date:
                try:
                    target_dt = datetime.strptime(search_date, "%Y-%m-%d")
                    rev_dt = datetime.strptime(r_date, "%Y-%m-%d")
                    diff_days = abs((rev_dt - target_dt).days)
                    if diff_days > 2:
                        continue
                except:
                    if r_date != search_date:
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
                "review_date": r_date,
                "review_time": "12:00:00",
                "matched_keywords": ", ".join(matched_kws) if matched_kws else "70% Comment Match"
            })

    except Exception as e:
        print(f"Selenium Maps scraping error: {e}", flush=True)
    finally:
        driver.quit()

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

if __name__ == "__main__":
    test_target = "https://maps.app.goo.gl/M85DzbtVUu5NfvHVA"
    test_date = "2026-09-14"
    test_rating = 5
    test_comment = "Aroma oils and gentle touch felt amazing at aroma Swedish massage spa."

    res = scrape_maps_reviews_selenium(
        target_input=test_target,
        search_date=test_date,
        rating=test_rating,
        keyword_text=test_comment
    )
    print("\n================== SCRAPE RESULT ==================")
    print(f"Success: {res['success']}")
    print(f"Place: {res['place_info']['title']}")
    print(f"Total Scanned: {res['total_scanned']}")
    print(f"Total Matched: {res['total_matched']}")
    for idx, r in enumerate(res['reviews']):
        u_name = r['user_name'].encode('ascii', 'replace').decode()
        txt = r['review_text'].encode('ascii', 'replace').decode()
        print(f"\nMatch #{idx+1}:")
        print(f"  Author: {u_name} (original len: {len(r['user_name'])})")
        print(f"  Rating: {r['rating']} stars")
        print(f"  Date: {r['review_date']}")
        print(f"  Content: {txt}")
        print(f"  Matched: {r['matched_keywords']}")

