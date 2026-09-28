import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = "https://maps.app.goo.gl/M85DzbtVUu5NfvHVA"
r = requests.head(url, allow_redirects=True, timeout=10)
clean_url = r.url.replace("entry=tts&", "").replace("entry=tts", "")

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
    print(f"Loading {clean_url[:80]}...")
    driver.get(clean_url)
    
    # 1. Reliable Reviews Opener
    for attempt in range(15):
        time.sleep(1)
        # Check if tabs exist
        tabs = driver.find_elements(By.CSS_SELECTOR, "button[role='tab']")
        if len(tabs) >= 2:
            print(f"Clicking Reviews tab at attempt {attempt+1}...")
            driver.execute_script("arguments[0].click();", tabs[1])
            break
        # Check star button
        stars = driver.find_elements(By.CSS_SELECTOR, "span.ceNzKf, span[aria-label*='stars']")
        if stars:
            print(f"Clicking star button ancestor at attempt {attempt+1}...")
            driver.execute_script("""
                let el = arguments[0];
                while (el && el.tagName !== 'BUTTON' && el.tagName !== 'DIV') {
                    el = el.parentElement;
                }
                if (el) el.click();
            """, stars[0])
            time.sleep(2)
            # After clicking star, click reviews tab
            rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')]")
            if rev_tabs:
                print("Clicking revealed Reviews tab...")
                driver.execute_script("arguments[0].click();", rev_tabs[0])
            break

    # 2. Wait for initial cards
    for w in range(12):
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if cards:
            print(f"Initial cards rendered at {w+1}s: {len(cards)}")
            break
        time.sleep(1)
        
    # 3. Click Sort -> Newest
    print("Finding Sort button...")
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
    print(f"Found {len(sort_btns)} sort buttons.")
    if sort_btns:
        btn_text = sort_btns[0].text.encode('ascii', 'ignore').decode()
        print(f"Clicking Sort button: '{btn_text}'", flush=True)
        driver.execute_script("arguments[0].click();", sort_btns[0])
        time.sleep(1.5)
        driver.save_screenshot("sort_menu_screenshot.png")
        
        # In Google Maps menu, find Newest
        menu_items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem'] | //div[contains(@class, 'action-menu-item')]")
        print(f"Sort menu options: {len(menu_items)}")
        for idx, mi in enumerate(menu_items):
            print(f"  Option {idx}: text='{mi.text}'")
            if "newest" in mi.text.lower() or idx == 1:
                print(f"Clicking Newest option ({mi.text})...")
                driver.execute_script("arguments[0].click();", mi)
                time.sleep(3)
                break
                
    driver.save_screenshot("after_sort_result.png")
    
    # 4. Extract all reviews
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"\nTotal extracted cards: {len(cards)}")
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
        print(f"[{idx+1}] {clean_author} ({date_str}): {clean_text}")

finally:
    driver.quit()
