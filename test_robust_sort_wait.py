import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = "https://www.google.com/maps/place/Mamta+Spa/@18.5606628,73.9192261,17z/data=!4m8!3m7!1s0x3bc2c16cf0625e73:0x5f36700060f07b8!8m2!3d18.5606628!4d73.9192261!9m1!1b1!16s%2Fg%2F11yw0p2qqr"

opts = Options()
opts.page_load_strategy = 'eager'
opts.add_argument('--headless=new')
opts.add_argument('--disable-gpu')
opts.add_argument('--no-sandbox')
opts.add_argument('--window-size=1600,1200')
opts.add_argument('--disable-blink-features=AutomationControlled')
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

d = webdriver.Chrome(options=opts)
try:
    d.get(url)
    
    def dismiss():
        btns = d.find_elements(By.XPATH, '//button[contains(., "Dismiss")]')
        if btns:
            d.execute_script("arguments[0].click();", btns[0])
            time.sleep(1)
            return True
        return False

    # 1. Wait up to 10s for sort button
    sort_btn = None
    for w in range(10):
        dismiss()
        btns = d.find_elements(By.XPATH, '//button[contains(@aria-label, "Sort") or contains(., "Sort") or contains(@class, "S9kvJb")]')
        if btns:
            sort_btn = btns[0]
            print(f"Sort button found at {w+1}s!", flush=True)
            break
        time.sleep(1)

    if sort_btn:
        for attempt in range(4):
            dismiss()
            print(f"Clicking sort button (attempt {attempt+1})...", flush=True)
            d.execute_script("arguments[0].click();", sort_btn)
            time.sleep(1.5)
            if dismiss():
                print("Modal dismissed, retrying sort click...", flush=True)
                continue

            items = d.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
            print(f"Menu items found: {len(items)}", flush=True)
            if len(items) >= 2:
                print("Clicking Newest (item 1)...", flush=True)
                d.execute_script("arguments[0].click();", items[1])
                print("Clicked Newest successfully!", flush=True)
                time.sleep(4)
                break

    # 2. Wait for cards
    cards = []
    for w in range(15):
        time.sleep(1)
        cards = d.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if cards:
            print(f"Cards loaded at {w+1}s: {len(cards)}", flush=True)
            break

    # 3. Print cards
    print(f"\n--- Extracted {len(cards)} cards ---")
    for idx, c in enumerate(cards):
        try:
            a = c.find_element(By.CSS_SELECTOR, 'div.d4r55').text.strip()
        except:
            a = "Unknown"
        try:
            t = c.find_element(By.CSS_SELECTOR, 'span.wiI7pd').text.strip()
        except:
            t = ""
        try:
            d_str = c.find_element(By.CSS_SELECTOR, 'span.rsqaWe').text.strip()
        except:
            d_str = ""
        clean_a = a.encode('ascii', 'replace').decode()
        clean_t = t.encode('ascii', 'replace').decode()
        print(f"[{idx+1}] {clean_a} ({d_str}): {clean_t[:60]}")

finally:
    d.quit()
