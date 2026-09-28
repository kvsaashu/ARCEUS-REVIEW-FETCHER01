import requests
import json
import time

url = "http://127.0.0.1:5000/api/fetch"
payload = {
    "service_type": "MAP",
    "target_id": "https://maps.app.goo.gl/M85DzbtVUu5NfvHVA",
    "search_date": "2026-09-14",
    "rating": 5,
    "keywords": "Aroma oils and gentle touch felt amazing at aroma Swedish massage spa.",
    "auto_save": True
}

t0 = time.time()
print("Sending request to /api/fetch...", flush=True)
resp = requests.post(url, json=payload, timeout=40)
elapsed = time.time() - t0

print(f"Status: {resp.status_code} in {elapsed:.2f}s")
data = resp.json()
print("Success:", data.get("success"))
print("Total scanned:", data.get("total_scanned"))
print("Total matched:", data.get("total_matched"))
for r in data.get("reviews", []):
    u = r["user_name"].encode("ascii", "replace").decode()
    t = r["review_text"].encode("ascii", "replace").decode()
    print(f"Matched Review by {u} ({r['rating']}* | {r['review_date']}): {t}")
