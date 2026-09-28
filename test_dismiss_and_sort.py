import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

url = "https://www.google.com/maps/place/Mamta+Spa/@18.5606628,73.9192261,17z/data=!4m8!3m7!1s0x3bc2c16cf0625e73:0x5f36700060f07b8!8m2!3d18.5606628!4d73.9192261!9m1!1b1!16s%2Fg%2F11yw0p2qqr"

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

d = webdriver.Chrome(options=opts)
try:
    d.get(url)
    time.sleep(4)

    # Helper to dismiss modal
    def dismiss_modal():
        d_btns = d.find_elements(By.XPATH, "//button[contains(., 'Dismiss') or contains(@aria-label, 'Dismiss')] | //span[contains(text(), 'Dismiss')]/ancestor::button")
        if d_btns:
            print("Found Dismiss button! Clicking it...")
            d.execute_script("arguments[0].click();", d_btns[0])
            time.sleep(1)
            return True
        return False

    dismiss_modal()

    # Robust Sort -> Newest loop
    for attempt in range(4):
        # Dismiss any existing modal first
        dismiss_modal()
        
        sort_btns = d.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
        if not sort_btns:
            print("No sort buttons found")
            break
        print(f"Attempt {attempt+1}: Clicking sort button...")
        d.execute_script("arguments[0].click();", sort_btns[0])
        time.sleep(1.5)

        # Check if modal intercepted the click
        if dismiss_modal():
            print(f"Modal intercepted sort click on attempt {attempt+1}, dismissed and retrying...")
            continue

        items = d.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
        print(f"Attempt {attempt+1}: Menu items found: {len(items)}")
        if items:
            for idx, mi in enumerate(items):
                txt = mi.text.encode('ascii', 'replace').decode()
                print(f"  [{idx}] text='{txt}'")
                if "newest" in txt.lower() or idx == 1:
                    print(f"Clicking item {idx} (Newest)...")
                    d.execute_script("arguments[0].click();", mi)
                    time.sleep(3)
                    break
            break

    cards = []
    for w in range(15):
        time.sleep(1)
        cards = d.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if cards:
            print(f"Cards rendered after {w+1}s: {len(cards)}")
            break

    d.save_screenshot("test_newest_dismissed_ok.png")
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
    d.quit()
