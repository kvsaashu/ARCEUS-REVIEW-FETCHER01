import time
from fetcher_map import resolve_maps_url
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

info = resolve_maps_url('https://maps.app.goo.gl/M85DzbtVUu5NfvHVA')
url = info['full_url']

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
    time.sleep(4)

    def dismiss():
        btns = d.find_elements(By.XPATH, '//button[contains(., "Dismiss")]')
        if btns:
            btns[0].click()
            time.sleep(1)
            return True
        return False

    dismiss()

    sort_btns = d.find_elements(By.XPATH, '//button[contains(@aria-label, "Sort") or contains(., "Sort")]')
    print("Sort btns:", len(sort_btns))
    if sort_btns:
        btn = sort_btns[0]
        # Get location of sort button
        loc = btn.location
        size = btn.size
        cx = int(loc['x'] + size['width'] / 2)
        cy = int(loc['y'] + size['height'] / 2)
        print(f"Clicking at ({cx}, {cy}) via ActionChains and CDP...")

        # ActionChains click
        try:
            ActionChains(d).move_to_element(btn).pause(0.2).click().perform()
            print("ActionChains click done")
        except Exception as e:
            print("ActionChains error:", e)

        time.sleep(1.5)
        dismiss()

        # Check menu items
        items = d.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
        print(f"Items via ActionChains: {len(items)}")

        if not items:
            # Try CDP real click
            d.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": cx, "y": cy})
            d.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": cx, "y": cy, "button": "left", "clickCount": 1})
            time.sleep(0.1)
            d.execute_cdp_cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": cx, "y": cy, "button": "left", "clickCount": 1})
            time.sleep(1.5)
            dismiss()
            items = d.find_elements(By.XPATH, '//*[@role="menuitemradio"] | //*[@role="menuitem"]')
            print(f"Items via CDP click: {len(items)}")

        if items:
            print("Clicking Newest (item 1)...")
            try:
                items[1].click()
            except:
                d.execute_script("arguments[0].click();", items[1])
            cards = []
            for w in range(15):
                time.sleep(1)
                cards = d.find_elements(By.CSS_SELECTOR, "div.jftiEf")
                if cards:
                    print(f"Cards after newest at {w+1}s: {len(cards)}")
                    break

            for idx, c in enumerate(cards[:10]):
                a = c.find_element(By.CSS_SELECTOR, 'div.d4r55').text.strip().encode('ascii', 'replace').decode()
                t = c.find_element(By.CSS_SELECTOR, 'span.wiI7pd').text.strip().encode('ascii', 'replace').decode()
                print(f" [{idx+1}] {a}: {t[:60]}")

finally:
    d.quit()
