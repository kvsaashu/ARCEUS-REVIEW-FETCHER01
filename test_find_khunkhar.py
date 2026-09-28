import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = "https://maps.app.goo.gl/M85DzbtVUu5NfvHVA"
try:
    r = requests.head(url, allow_redirects=True, timeout=10)
    full_url = r.url
except:
    full_url = url
clean_url = full_url.replace("entry=tts&", "").replace("entry=tts", "")
print(f"Loading {clean_url[:80]}...")

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

try:
    driver.get(clean_url)
    
    # 1. Reliable loop to open Reviews tab
    reviews_opened = False
    for attempt in range(15):
        time.sleep(1)
        # Check direct Reviews tab
        rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')] | (//button[@role='tab'])[2]")
        if rev_tabs:
            print(f"Found Reviews tab at attempt {attempt+1}! Clicking...")
            driver.execute_script("arguments[0].click();", rev_tabs[0])
            reviews_opened = True
            time.sleep(2)
            break
            
        # Check star button
        star_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'stars') or contains(@aria-label, 'rating')] | //span[contains(@aria-label, 'stars')]/ancestor::button | //span[contains(@class, 'ceNzKf')]/ancestor::button")
        if star_btns:
            print(f"Clicking star button at attempt {attempt+1}...")
            driver.execute_script("arguments[0].click();", star_btns[0])
            time.sleep(1.5)
            # Check revealed tab
            rev_tabs_after = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')]")
            if rev_tabs_after:
                print("Clicking revealed Reviews tab...")
                driver.execute_script("arguments[0].click();", rev_tabs_after[0])
                time.sleep(2)
            reviews_opened = True
            break
            
    # 2. Wait for initial review cards
    cards = []
    for w in range(12):
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if cards:
            print(f"Cards rendered at {w+1}s: {len(cards)}")
            break
        time.sleep(1)
        
    # 3. Try to click Sort -> Newest
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
    if sort_btns:
        print("Clicking Sort button...")
        driver.execute_script("arguments[0].click();", sort_btns[0])
        time.sleep(1.5)
        
        # Click 2nd item in menu (Newest)
        menu_items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
        print(f"Menu items found: {len(menu_items)}")
        for idx, m in enumerate(menu_items):
            if "newest" in m.text.lower() or idx == 1:
                print(f"Clicking menu item {idx} (Newest)...")
                driver.execute_script("arguments[0].click();", m)
                time.sleep(2.5)
                break
                
    # 4. Scroll to load more cards
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    for s in range(6):
        if not cards:
            break
        last_card = cards[-1]
        driver.execute_script("arguments[0].scrollIntoView(true);", last_card)
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mouseWheel",
            "x": 250,
            "y": 700,
            "deltaX": 0,
            "deltaY": 1500
        })
        time.sleep(1.2)
        new_cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if len(new_cards) == len(cards):
            break
        cards = new_cards
        
    print(f"\nTotal cards loaded: {len(cards)}")
    for idx, c in enumerate(cards):
        try:
            author = c.find_element(By.CSS_SELECTOR, "div.d4r55").text.strip()
        except:
            author = "Unknown"
        try:
            text = c.find_element(By.CSS_SELECTOR, "span.wiI7pd").text.strip()
        except:
            text = ""
        try:
            date_str = c.find_element(By.CSS_SELECTOR, "span.rsqaWe").text.strip()
        except:
            date_str = ""
            
        clean_author = author.encode('ascii', 'replace').decode()
        clean_text = text.replace('\n', ' ').encode('ascii', 'replace').decode()
        
        is_target = "aroma oils and gentle touch" in text.lower() or "andrew" in author.lower() or "khunkhar" in clean_author.lower()
        prefix = ">>> [TARGET FOUND] " if is_target else "    "
        print(f"{prefix}[{idx+1}] {clean_author} ({date_str}): {clean_text}")

finally:
    driver.quit()

