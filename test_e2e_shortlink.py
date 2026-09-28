import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def convert_to_direct_reviews_url(target: str) -> str:
    full_url = target.strip()
    if "goo.gl" in target or "maps.app.goo.gl" in target:
        try:
            r = requests.head(target, allow_redirects=True, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }, timeout=10)
            full_url = r.url
        except Exception as e:
            print("Redirect err:", e)

    clean = full_url.replace("entry=tts&", "").replace("entry=tts", "")
    
    # Extract place components
    m_title = re.search(r'/place/([^/@]+)', clean)
    title = m_title.group(1) if m_title else "Place"

    m_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', clean)
    lat, lng = m_coords.groups() if m_coords else ("0", "0")

    m_hex = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', clean)
    hex_id = m_hex.group(1) if m_hex else ""

    m_feat = re.search(r'(!16s[^!&?]+)', clean)
    feat = m_feat.group(1) if m_feat else ""

    if hex_id and lat != "0":
        direct = f"https://www.google.com/maps/place/{title}/@{lat},{lng},17z/data=!4m8!3m7!1s{hex_id}!8m2!3d{lat}!4d{lng}!9m1!1b1{feat}"
        return direct

    # Fallback to appending reviews flag if not matchable
    return clean

short_url = "https://maps.app.goo.gl/M85DzbtVUu5NfvHVA"
direct_url = convert_to_direct_reviews_url(short_url)
print("Generated direct URL:\n", direct_url)

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
    driver.get(direct_url)
    time.sleep(4)

    # Check for signin modal and dismiss if present
    dismiss_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Dismiss') or contains(@aria-label, 'Dismiss')]")
    if dismiss_btns:
        print("Dismissing sign-in modal...")
        driver.execute_script("arguments[0].click();", dismiss_btns[0])
        time.sleep(1)

    # Click Sort button
    sort_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Sort') or contains(., 'Sort')]")
    print(f"Sort buttons found: {len(sort_btns)}")
    if sort_btns:
        btn = sort_btns[0]
        print(f"Clicking sort button...")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)

        # Click 2nd item in menu (Newest)
        items = driver.find_elements(By.XPATH, "//*[@role='menuitemradio'] | //*[@role='menuitem']")
        print(f"Menu items: {len(items)}")
        for idx, mi in enumerate(items):
            print(f"  Item {idx}: '{mi.text}'")
            if "newest" in mi.text.lower() or idx == 1:
                driver.execute_script("arguments[0].click();", mi)
                print(f"Selected item {idx} (Newest)!")
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

