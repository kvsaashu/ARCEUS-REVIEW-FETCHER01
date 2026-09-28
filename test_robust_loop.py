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
    
    # Wait for place panel and open reviews
    print("Waiting for place card and reviews trigger...")
    opened = False
    for attempt in range(20):
        time.sleep(1)
        # Check if Reviews tab is directly available
        rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')] | (//button[@role='tab'])[2]")
        if rev_tabs:
            print(f"Found Reviews tab at attempt {attempt+1}! Clicking it...")
            driver.execute_script("arguments[0].click();", rev_tabs[0])
            opened = True
            time.sleep(2)
            break
            
        # Check if star trigger exists to reveal reviews
        stars = driver.find_elements(By.CSS_SELECTOR, "span.ceNzKf, span[aria-label*='stars']")
        if stars:
            print(f"Found stars trigger at attempt {attempt+1}! Clicking parent button...")
            driver.execute_script("""
                let el = arguments[0];
                while (el && el.tagName !== 'BUTTON' && el.tagName !== 'DIV') {
                    el = el.parentElement;
                }
                if (el) el.click();
                else arguments[0].click();
            """, stars[0])
            time.sleep(2)
            # Now click the revealed Reviews tab if available
            rev_tabs_after = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')]")
            if rev_tabs_after:
                print("Clicking revealed Reviews tab...")
                driver.execute_script("arguments[0].click();", rev_tabs_after[0])
                time.sleep(2)
            opened = True
            break
            
    # Wait for review cards
    cards = []
    for w in range(12):
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if cards:
            print(f"SUCCESS! Cards rendered at {w+1}s: {len(cards)}")
            break
        time.sleep(1)
        
    driver.save_screenshot("test_opened_reviews.png")
    
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

