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
full_url = resp.url
print("Resolved:", full_url[:80])

clean_url = full_url.replace("entry=tts&", "").replace("entry=tts", "")
if "!9m1!1b1" not in clean_url:
    if "/data=" in clean_url:
        clean_url = re.sub(r'(/data=[^?]+)', r'\1!9m1!1b1', clean_url)
    elif "?" in clean_url:
        clean_url = clean_url.replace("?", "/data=!9m1!1b1?")
    else:
        clean_url = clean_url + "/data=!9m1!1b1"

print("Modified URL:", clean_url[:90])

opts = Options()
opts.page_load_strategy = "eager"
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1600,1200")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

d = webdriver.Chrome(options=opts)
try:
    d.get(clean_url)
    time.sleep(4)
    cards = d.find_elements(By.CSS_SELECTOR, "div.jftiEf")
    sort_btns = d.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
    print(f"Cards found: {len(cards)}, Sort buttons found: {len(sort_btns)}")
finally:
    d.quit()

