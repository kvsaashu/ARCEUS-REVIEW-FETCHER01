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
    driver.get(clean_url)
    
    # 1. Open reviews tab via robust logic
    for attempt in range(20):
        time.sleep(1)
        rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')] | (//button[@role='tab'])[2]")
        if rev_tabs:
            driver.execute_script("arguments[0].click();", rev_tabs[0])
            break
        stars = driver.find_elements(By.CSS_SELECTOR, "span.ceNzKf, span[aria-label*='stars']")
        if stars:
            driver.execute_script("""
                let el = arguments[0];
                while (el && el.tagName !== 'BUTTON' && el.tagName !== 'DIV') {
                    el = el.parentElement;
                }
                if (el) el.click();
                else arguments[0].click();
            """, stars[0])
            time.sleep(1.5)
            rev_tabs_after = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')]")
            if rev_tabs_after:
                driver.execute_script("arguments[0].click();", rev_tabs_after[0])
            break

    # Wait for cards to appear
    for _ in range(12):
        if driver.find_elements(By.CSS_SELECTOR, "div.jftiEf"):
            break
        time.sleep(1)

    print("Reviews loaded. Now inspecting Sort button...")
    # Find the button containing text 'Sort'
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Sort') or contains(@aria-label, 'Sort') or contains(@aria-label, 'sort')]")
    print(f"Found {len(sort_btns)} Sort buttons.")
    if sort_btns:
        btn = sort_btns[0]
        print(f"Sort button: tag={btn.tag_name}, aria='{btn.get_attribute('aria-label')}', text='{btn.text}'")
        # Click sort button
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
        driver.save_screenshot("sort_clicked.png")
        
        # In the popup, find the Newest option
        # Try finding role='menuitemradio' or elements with text 'Newest'
        newest = driver.find_elements(By.XPATH, "//*[@role='menuitemradio' and contains(., 'Newest')] | //div[text()='Newest'] | //div[contains(., 'Newest') and @role='menuitemradio']")
        if not newest:
            # Check all items in role='menu'
            menu_items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
            print(f"Menu items found: {len(menu_items)}")
            for idx, m in enumerate(menu_items):
                print(f"  [{idx}] text='{m.text}'")
                if "newest" in m.text.lower() or idx == 1:
                    newest = [m]
                    break
                    
        if newest:
            print("Clicking Newest option:", newest[0].text)
            driver.execute_script("arguments[0].click();", newest[0])
            time.sleep(3)
            driver.save_screenshot("after_newest_selected.png")
        else:
            print("Could not find Newest option in popup!")
            
    # Print the resulting cards
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"\nExtracted {len(cards)} cards:")
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

