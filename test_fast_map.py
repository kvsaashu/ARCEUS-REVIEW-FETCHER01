import time
from datetime import datetime
from fetcher_map import resolve_maps_url, parse_relative_date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

t0 = time.time()
info = resolve_maps_url('https://maps.app.goo.gl/M85DzbtVUu5NfvHVA')
clean_url = info['full_url']

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

driver = webdriver.Chrome(options=opts)
try:
    print(f"[{time.time()-t0:.2f}s] Loading page...", flush=True)
    driver.get(clean_url)
    
    def dismiss_modal():
        try:
            btns = driver.find_elements(By.XPATH, '//button[contains(., "Dismiss")]')
            if btns:
                btns[0].click()
                return True
        except:
            pass
        return False

    sort_btn = None
    for _ in range(10):
        dismiss_modal()
        btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Sort") or contains(., "Sort")]')
        if btns:
            sort_btn = btns[0]
            break
        time.sleep(0.4)

    print(f"[{time.time()-t0:.2f}s] Sort btn found: {bool(sort_btn)}", flush=True)
    if sort_btn:
        ActionChains(driver).move_to_element(sort_btn).pause(0.1).click().perform()
        items = []
        for _ in range(6):
            dismiss_modal()
            items = driver.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
            if len(items) >= 2:
                break
            time.sleep(0.3)
        
        print(f"[{time.time()-t0:.2f}s] Menu items found: {len(items)}", flush=True)
        if len(items) >= 2:
            try:
                items[1].click()
            except:
                driver.execute_script("arguments[0].click();", items[1])
            print(f"[{time.time()-t0:.2f}s] Clicked Newest!", flush=True)

    # Poll for cards to render after sort (up to 6s)
    cards = []
    for _ in range(12):
        time.sleep(0.5)
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        if cards:
            break
    print(f"[{time.time()-t0:.2f}s] Cards loaded after sort: {len(cards)}", flush=True)

    # Fast scroll loop with date check
    search_date = "2026-09-14"
    target_dt = datetime.strptime(search_date, "%Y-%m-%d")
    
    for s in range(4):
        # Check oldest card date
        if cards:
            last_card = cards[-1]
            try:
                d_str = last_card.find_element(By.CSS_SELECTOR, "span.rsqaWe").text.strip()
                oldest_date = parse_relative_date(d_str)
                oldest_dt = datetime.strptime(oldest_date, "%Y-%m-%d")
                if (target_dt - oldest_dt).days > 2:
                    print(f"[{time.time()-t0:.2f}s] Oldest review date is {oldest_date} (older than target {search_date}). Stopping scroll early at scroll {s}!", flush=True)
                    break
            except Exception as e:
                pass
            
            driver.execute_script("arguments[0].scrollIntoView(true);", last_card)
            driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                "type": "mouseWheel",
                "x": 250,
                "y": 700,
                "deltaX": 0,
                "deltaY": 1200
            })
            time.sleep(0.6)
            new_cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
            if len(new_cards) == len(cards):
                break
            cards = new_cards

    print(f"[{time.time()-t0:.2f}s] Total cards to parse: {len(cards)}", flush=True)
    # Check if target review is present
    found = False
    for idx, c in enumerate(cards):
        try:
            t = c.find_element(By.CSS_SELECTOR, 'span.wiI7pd').text.strip()
        except:
            t = ""
        try:
            a = c.find_element(By.CSS_SELECTOR, 'div.d4r55').text.strip()
        except:
            a = "Unknown"
        clean_a = a.encode('ascii', 'replace').decode()
        clean_t = t.encode('ascii', 'replace').decode()
        print(f"[{idx+1}] {clean_a}: {clean_t[:60]}", flush=True)
        if "Aroma oils and gentle touch" in t or "aroma Swedish" in t:
            print(f"[{time.time()-t0:.2f}s] FOUND TARGET REVIEW! Card #{idx+1} by {clean_a}: {clean_t[:60]}", flush=True)
            found = True


    print(f"[{time.time()-t0:.2f}s] Finished! Found: {found}", flush=True)
finally:
    driver.quit()
