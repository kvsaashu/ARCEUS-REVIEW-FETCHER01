import sys
from datetime import datetime
from matcher import (
    match_keywords, match_single_keyword, match_symbol_trailing,
    match_member_name, match_ending_hint, calculate_comment_similarity
)
from fetcher_map import parse_relative_date, resolve_maps_url
from fetcher_app import fetch_app_reviews
from database import save_review, get_recent_reviews
from integrations import generate_csv_string

def run_tests():
    print("=== 1. TESTING COMMENT & FUZZY MATCHER ===")
    
    # 70% comment similarity
    t1 = "Warm oils and expert hands gave comfort at this massage spa.."
    r1 = "Warm oils and gentle strokes gave comfort at this massage spa"
    sim = calculate_comment_similarity(t1, r1)
    print(f"Similarity score: {sim:.2f}")
    assert sim >= 0.70, "70% comment similarity failed"
    
    # Fuzzy & Typo tolerance
    assert match_single_keyword("FAST PAYMENT", "fast payment") == True, "Case-insensitive failed"
    assert match_single_keyword("fast payment.", "fast payment") == True, "Punctuation tolerance failed"
    assert match_single_keyword("fast paymnt received", "fast payment") == True, "Typo tolerance failed"
    assert match_single_keyword("great app #ARCEU", "#ARCEUS") == True, "Missing alphabet tolerance failed"
    
    # Ending hint tests
    assert match_ending_hint("Good service..", "..") == True, "Ending hint .. failed"
    assert match_ending_hint("Good service.", "..") == True, "Lenient single dot failed"
    assert match_ending_hint("Good service.. 😊", "..") == True, "Ending hint with emoji failed"
    assert match_ending_hint("Good service but not .. cool", "..") == False, "Middle dots falsely matched as ending"
    print("[PASS] Matcher tests passed!")

    print("\n=== 2. TESTING MAPS RELATIVE DATE PARSER ===")
    today_str = datetime.now().strftime("%Y-%m-%d")
    assert parse_relative_date("just now") == today_str
    assert parse_relative_date("2 hours ago") == today_str
    print("[PASS] Relative date parser passed!")

    print("\n=== 3. TESTING DATABASE & CSV EXPORT ===")
    sample = {
        "service_type": "APP",
        "target_id": "com.test.app",
        "target_name": "Test App",
        "review_id": "rev_test_101",
        "user_name": "Test User",
        "user_image": "",
        "rating": 5,
        "review_text": "Great application..",
        "highlighted_text": "Great application<mark class='kw-highlight'>..</mark>",
        "review_date": "2026-09-14",
        "review_time": "14:00:00",
        "matched_keywords": ".."
    }
    save_review(sample)
    csv_out = generate_csv_string([sample])
    assert "Test User" in csv_out
    assert "LIVE" in csv_out
    print("[PASS] Database and CSV export passed!")

    print("\n*** ALL TESTS PASSED SUCCESSFULLY! ***")

if __name__ == "__main__":
    run_tests()
