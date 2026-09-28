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
    
    # 1. Open reviews tab
    for attempt in range(15):
        time.sleep(1)
        rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or text()='Reviews' or contains(., 'Reviews')] | (//button[@role='tab'])[2]")
        if rev_tabs:
            driver.execute_script("arguments[0].click();", rev_tabs[0])
            break
            
    # Wait for cards
    for _ in range(10):
        if driver.find_elements(By.CSS_SELECTOR, "div.jftiEf"):
            break
        time.sleep(1)
        
    print("Reviews loaded. Now looking for Sort button...")
    # Find sort button (usually has text Sort or aria-label containing sort or class ghp-sort)
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort') or contains(@data-value, 'Sort')]")
    print(f"Sort buttons found: {len(sort_btns)}")
    
    if sort_btns:
        print("Clicking Sort button via Action/JS...")
        driver.execute_script("arguments[0].click();", sort_btns[0])
        time.sleep(1.5)
        driver.save_screenshot("sort_dropdown_open.png")
        
        # Look for Newest option
        # In Google Maps, the sort options are role='menuitemradio' or div with text 'Newest'
        newest_items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio' and (contains(., 'Newest') or contains(@data-index, '1'))] | //div[text()='Newest'] | //span[text()='Newest']")
        print(f"Newest items found: {len(newest_items)}")
        
        if not newest_items:
            # Check all elements in any menu
            all_menu_items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio' or @role='menuitem']")
            print(f"All menu items count: {len(all_menu_items)}")
            for idx, m in enumerate(all_menu_items):
                print(f"  Menu {idx}: text='{m.text}' aria='{m.get_attribute('aria-label')}'")
                if "newest" in m.text.lower() or idx == 1:
                    driver.execute_script("arguments[0].click();", m)
                    print(f"Clicked menu item {idx}!")
                    time.sleep(3)
                    break
        else:
            driver.execute_script("arguments[0].click();", newest_items[0])
            print("Clicked Newest item!")
            time.sleep(3)
            
    # Now extract the sorted cards
    sorted_cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"\n--- Extracted {len(sorted_cards)} cards after sort ---")
    for idx, c in enumerate(sorted_cards):
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

