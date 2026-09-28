import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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
    
    # Dismiss any initial modal
    for _ in range(5):
        btns = d.find_elements(By.XPATH, '//button[contains(., "Dismiss")]')
        if btns:
            btns[0].click()
            break
        time.sleep(0.3)

    sort_btn = None
    for _ in range(10):
        btns = d.find_elements(By.XPATH, '//button[contains(@aria-label, "Sort") or contains(., "Sort")]')
        if btns:
            sort_btn = btns[0]
            break
        time.sleep(0.3)

    print("Sort btn found:", bool(sort_btn))
    items = []
    if sort_btn:
        # 1. Try ActionChains
        try:
            ActionChains(d).move_to_element(sort_btn).pause(0.1).click().perform()
            for _ in range(6):
                items = d.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
                if len(items) >= 2:
                    break
                time.sleep(0.25)
            print("Items after ActionChains:", len(items))
        except Exception as e:
            print("ActionChains error:", e)

        # 2. If not found, try CDP click
        if len(items) < 2:
            loc = sort_btn.location
            size = sort_btn.size
            cx = int(loc['x'] + size['width'] / 2)
            cy = int(loc['y'] + size['height'] / 2)
            print(f"Trying CDP click at ({cx}, {cy})...")
            d.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": cx, "y": cy})
            d.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": cx, "y": cy, "button": "left", "clickCount": 1})
            time.sleep(0.05)
            d.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": cx, "y": cy, "button": "left", "clickCount": 1})
            for _ in range(6):
                items = d.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
                if len(items) >= 2:
                    break
                time.sleep(0.25)
            print("Items after CDP click:", len(items))

        # 3. If still not found, try keyboard Enter / Space
        if len(items) < 2:
            print("Trying keyboard Keys.ENTER...")
            sort_btn.send_keys(Keys.ENTER)
            for _ in range(6):
                items = d.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
                if len(items) >= 2:
                    break
                time.sleep(0.25)
            print("Items after Keys.ENTER:", len(items))

        print("FINAL items count:", len(items))
        if len(items) >= 2:
            try:
                items[1].click()
            except:
                d.execute_script("arguments[0].click();", items[1])
            print("Clicked Newest successfully!")
            time.sleep(2)
            cards = d.find_elements(By.CSS_SELECTOR, "div.jftiEf")
            print("Cards loaded:", len(cards))
finally:
    d.quit()
