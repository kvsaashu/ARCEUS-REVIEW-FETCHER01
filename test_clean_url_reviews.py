import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = "https://maps.app.goo.gl/M85DzbtVUu5NfvHVA"
resp = requests.head(url, allow_redirects=True, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}, timeout=10)
raw_url = resp.url
print("Raw resolved URL:", raw_url)

# Clean URL:
# 1. Strip query string
base = raw_url.split("?")[0]
# 2. Remove satellite parameter !3m1!1e3 or !1e3
base = re.sub(r'!3m1!1e3', '', base)
base = re.sub(r'!1e3', '', base)
# 3. Remove !18m1!1e1
base = re.sub(r'!18m1!1e1', '', base)
# 4. Insert !9m1!1b1 if not present
if "!9m1!1b1" not in base:
    # Insert before !16s if present, else append
    if "!16s" in base:
        base = base.replace("!16s", "!9m1!1b1!16s")
    else:
        base = base + "!9m1!1b1"

print("Transformed reviews URL:", base)

opts = Options()
opts.page_load_strategy = "eager"
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
opts.add_argument("--no-sandbox")
opts.add_argument("--window-size=1600,1200")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=opts)
try:
    driver.get(base)
    time.sleep(4)
    driver.save_screenshot("test_transformed_page.png")
    
    # Check cards
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"Cards found directly: {len(cards)}")
    
    # Check sort buttons
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
    print(f"Sort buttons found: {len(sort_btns)}")
    
    if sort_btns:
        driver.execute_script("arguments[0].click();", sort_btns[0])
        time.sleep(1.5)
        menu_items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
        print(f"Menu items: {len(menu_items)}")
        for idx, mi in enumerate(menu_items):
            print(f"  Item {idx}: '{mi.text}'")
            if "newest" in mi.text.lower() or idx == 1:
                driver.execute_script("arguments[0].click();", mi)
                print(f"Selected item {idx}!")
                time.sleep(3)
                break
                
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        print(f"\n--- Extracted {len(cards)} cards after sort ---")
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

