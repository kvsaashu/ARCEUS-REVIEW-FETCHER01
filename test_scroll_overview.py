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
    time.sleep(5)
    
    # Scroll down the left panel using CDP mouse wheel
    for s in range(10):
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mouseWheel",
            "x": 200,
            "y": 600,
            "deltaX": 0,
            "deltaY": 1500
        })
        time.sleep(1)
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        body = driver.find_element(By.TAG_NAME, "body").text
        has_aroma = "Aroma oils" in body
        has_andrew = "Andrew" in body
        has_khunkhar = "[खूंखार]" in body
        print(f"Scroll {s+1}: Cards={len(cards)}, 'Aroma oils'={has_aroma}, 'Andrew'={has_andrew}, 'khunkhar'={has_khunkhar}", flush=True)
        if cards or has_aroma or has_andrew:
            driver.save_screenshot("found_by_scrolling.png")
            print("Found reviews by scrolling panel!")
            break
            
    driver.save_screenshot("scroll_bottom.png")
finally:
    driver.quit()
