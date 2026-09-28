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
    
    # 1. Scroll down once to bring "More reviews" into view
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
        "type": "mouseWheel",
        "x": 200,
        "y": 600,
        "deltaX": 0,
        "deltaY": 1500
    })
    time.sleep(1.5)
    
    # 2. Look for "More reviews" button
    more_rev_btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'More reviews') or contains(., 'More reviews') or contains(., 'more reviews')]")
    print(f"Found {len(more_rev_btns)} 'More reviews' elements.")
    if more_rev_btns:
        print("Clicking 'More reviews' button:", more_rev_btns[0].text)
        driver.execute_script("arguments[0].click();", more_rev_btns[0])
        time.sleep(3)
        driver.save_screenshot("after_more_reviews_clicked.png")
        print("Saved after_more_reviews_clicked.png")
        
    # Check what reviews are loaded now
    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    print(f"Total cards found after 'More reviews': {len(cards)}")
    for idx, c in enumerate(cards[:10]):
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

