from fetcher_map import fetch_map_reviews

res = fetch_map_reviews(
    target_input="https://maps.app.goo.gl/M85DzbtVUu5NfvHVA",
    search_date="2026-09-14",
    rating=5,
    keyword_text="Aroma oils and gentle touch felt amazing at aroma Swedish massage spa."
)

print("Total scanned:", res.get("total_scanned"))
print("Total matched:", res.get("total_matched"))
for r in res.get("reviews", []):
    u = r["user_name"].encode("ascii", "replace").decode()
    t = r["review_text"].encode("ascii", "replace").decode()
    print(f"Match: {u} ({r['rating']} stars, {r['review_date']}): {t}")
