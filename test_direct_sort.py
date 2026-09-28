import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = "https://www.google.com/maps/place/Mamta+Spa/@18.5606628,73.9192261,17z/data=!4m8!3m7!1s0x3bc2c16cf0625e73:0x5f36700060f07b8!8m2!3d18.5606628!4d73.9192261!9m1!1b1!16s%2Fg%2F11yw0p2qqr"

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
    driver.get(url)
    time.sleep(4)
    
    # Click Sort button
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
    print(f"Sort buttons found: {len(sort_btns)}")
    if sort_btns:
        btn = sort_btns[0]
        print(f"Clicking sort button (aria='{btn.get_attribute('aria-label')}')")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
        
        # Click 2nd item in menu (Newest)
        items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
        print(f"Menu items: {len(items)}")
        for idx, mi in enumerate(items):
            print(f"  Item {idx}: '{mi.text}'")
            if "newest" in mi.text.lower() or idx == 1:
                driver.execute_script("arguments[0].click();", mi)
                print(f"Selected item {idx}!")
                time.sleep(3)
                break
                
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"\n--- Extracted {len(cards)} sorted cards ---")
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

