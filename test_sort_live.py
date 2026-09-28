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
    print(f"Loading {clean_url[:80]}...")
    driver.get(clean_url)
    time.sleep(4)
    
    # Scroll down to reveal reviews
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
        "type": "mouseWheel",
        "x": 200,
        "y": 600,
        "deltaX": 0,
        "deltaY": 1500
    })
    time.sleep(2)
    
    # Find all buttons now visible
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"Total buttons after scroll: {len(buttons)}")
    sort_btn = None
    for b in buttons:
        aria = (b.get_attribute("aria-label") or "").lower()
        txt = b.text.strip().lower()
        if "sort" in aria or "sort" in txt:
            sort_btn = b
            btn_txt = b.text.encode('ascii', 'ignore').decode()
            print(f"Found sort button: tag={b.tag_name}, aria='{b.get_attribute('aria-label')}', text='{btn_txt}'", flush=True)
            break
            
    if sort_btn:
        print("Clicking Sort button...")
        # Dispatch real mouse click on the sort button via CDP or JS
        driver.execute_script("arguments[0].click();", sort_btn)
        time.sleep(2)
        driver.save_screenshot("sort_menu_opened_live.png")
        print("Saved sort_menu_opened_live.png")
        
        # Check all visible elements with text 'Newest'
        newest = driver.find_elements(By.XPATH, "//*[text()='Newest' or contains(text(), 'Newest')]")
        print(f"Elements containing 'Newest': {len(newest)}")
        for idx, n in enumerate(newest):
            print(f"  [{idx}] tag={n.tag_name} class='{n.get_attribute('class')}' text='{n.text}'")
            try:
                driver.execute_script("arguments[0].click();", n)
                print(f"  Clicked newest element [{idx}]!")
                time.sleep(3)
                break
            except Exception as e:
                print("Click err:", e)
                
        driver.save_screenshot("after_click_newest_live.png")
        
    # Extract all reviews
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"\nFinal extracted cards: {len(cards)}")
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
        print(f"[{idx+1}] {clean_author} ({date_str}): {clean_text[:70]}")
        
finally:
    driver.quit()
