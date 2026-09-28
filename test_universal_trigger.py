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
    time.sleep(3)
    
    # Let's find ANY clickable review trigger
    print("Looking for review triggers...")
    triggers = driver.find_elements(By.XPATH, """
        //button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews') or contains(., 'समीक्षा')] |
        //button[@role='tab' and (contains(., 'Reviews') or contains(., 'समीक्षा'))] |
        //div[@role='tab' and contains(., 'Reviews')] |
        //span[contains(@aria-label, 'stars')]/ancestor::button |
        //span[contains(@aria-label, 'stars')]/ancestor::div[@role='button']
    """)
    print(f"Triggers found: {len(triggers)}")
    for idx, t in enumerate(triggers):
        print(f"Trigger {idx}: tag={t.tag_name}, aria='{t.get_attribute('aria-label')}', text='{t.text}'")
        
    # Click the first matching trigger
    for t in triggers:
        try:
            driver.execute_script("arguments[0].click();", t)
            print("Clicked trigger successfully!")
            time.sleep(2)
            break
        except Exception as e:
            print("Click error:", e)
            
    # Also check if another tab click is needed
    rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')]")
    if rev_tabs:
        print("Clicking specific Reviews tab...")
        driver.execute_script("arguments[0].click();", rev_tabs[0])
        time.sleep(2)
        
    # Wait for cards
    cards = []
    for s in range(12):
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if cards:
            print(f"Cards found at {s+1}s: {len(cards)}")
            break
        time.sleep(1)
        
    driver.save_screenshot("test_triggers_result.png")
    
    # Print all cards
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

