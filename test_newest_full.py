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
print("Navigating to:", clean_url[:80])

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
    
    # 1. Open Reviews tab
    opened = False
    for attempt in range(20):
        time.sleep(1)
        # Check direct tab
        rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')] | (//button[@role='tab'])[2]")
        if rev_tabs:
            print(f"Found Reviews tab at attempt {attempt+1}! Clicking it...")
            driver.execute_script("arguments[0].click();", rev_tabs[0])
            opened = True
            time.sleep(2)
            break
            
        # Check star button ancestor
        star_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'stars') or contains(@aria-label, 'rating')] | //span[contains(@aria-label, 'stars')]/ancestor::button | //span[contains(@class, 'ceNzKf')]/ancestor::button")
        if star_btns:
            print(f"Found star button at attempt {attempt+1}! Clicking it...")
            driver.execute_script("arguments[0].click();", star_btns[0])
            time.sleep(2)
            rev_tabs_after = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')]")
            if rev_tabs_after:
                print("Clicking revealed Reviews tab...")
                driver.execute_script("arguments[0].click();", rev_tabs_after[0])
                time.sleep(2)
            opened = True
            break
            
    # 2. Wait for initial cards
    for _ in range(10):
        if driver.find_elements(By.CSS_SELECTOR, "div.jftiEf"):
            break
        time.sleep(1)
        
    print("Reviews open. Now trying to sort by Newest...")
    # Find sort button
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Sort') or contains(@aria-label, 'Sort') or @data-value='Sort']")
    print(f"Sort buttons found: {len(sort_btns)}")
    if sort_btns:
        print("Clicking Sort button...")
        driver.execute_script("arguments[0].click();", sort_btns[0])
        time.sleep(1.5)
        
        # Click Newest
        # In Google Maps, menuitemradio index 1 is Newest
        menu_items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
        print(f"Found {len(menu_items)} sort menu items:")
        for idx, m in enumerate(menu_items):
            print(f"  [{idx}] '{m.text}'")
            if "newest" in m.text.lower() or idx == 1:
                driver.execute_script("arguments[0].click();", m)
                print(f"Clicked menu item {idx} (Newest)!")
                time.sleep(3)
                break
                
    # 3. Extract cards
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"\n--- Extracted {len(cards)} cards ---")
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

