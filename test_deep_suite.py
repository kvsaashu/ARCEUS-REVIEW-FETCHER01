import os
import sys
import unittest
import threading
import concurrent.futures
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from matcher import (
    match_keywords, match_single_keyword, match_ending_hint,
    match_member_name, extract_keyword_list, highlight_matches
)
from database import (
    init_db, get_db, save_review, get_recent_reviews,
    set_setting, get_setting, create_campaign_task,
    get_campaign_tasks, get_campaign_task_by_id, delete_campaign_task
)
from fetcher_app import extract_package_id, format_review_date
from fetcher_batch import detect_service_type, generate_batch_csv_string
from integrations import generate_csv_string


class TestMatcherEngine(unittest.TestCase):
    """Deep verification of the review matching engine."""

    def test_exact_comment_match_app_mode(self):
        target = "Found the sign up process straightforward and the app loads fast on my older phone"
        review = "Found the sign up process straightforward and the app loads fast on my older phone"
        matched, kws = match_keywords(review, target, is_app_mode=True)
        self.assertTrue(matched)
        self.assertEqual(len(kws), 1)

    def test_case_insensitivity(self):
        target = "GREAT SERVICE AND FAST DELIVERY"
        review = "great service and fast delivery"
        matched, kws = match_keywords(review, target, is_app_mode=True)
        self.assertTrue(matched)

    def test_trailing_punctuation_and_commas(self):
        target = "Signing up was simple and I got straight into my first walk,"
        review = "Signing up was simple and I got straight into my first walk."
        matched, kws = match_keywords(review, target, is_app_mode=True)
        self.assertTrue(matched)

    def test_emoji_preservation(self):
        target = "setup took less than five minutes 📱,"
        review = "setup took less than five minutes 📱"
        matched, kws = match_keywords(review, target, is_app_mode=True)
        self.assertTrue(matched)

    def test_ending_hint_and_tags(self):
        # Hint tag match
        self.assertTrue(match_ending_hint("Great experience overall #ARCEUS", "#ARCEUS"))
        self.assertTrue(match_ending_hint("Great experience overall #arceus", "#ARCEUS"))
        self.assertTrue(match_ending_hint("Service was very nice..", ".."))
        self.assertTrue(match_ending_hint("Nice work done.", ".."))  # Dot tolerance

    def test_google_play_truncated_review_tolerance(self):
        # Google Play cuts reviews at ~500 chars
        target = "This is a very long review where the user wrote extensive feedback about everything from login to checkout and how fast it loaded across all devices and phones and tablets without any crash or slowdown or issues whatsoever."
        truncated = target[:len(target) - 30]  # Truncated tail
        self.assertTrue(match_single_keyword(truncated, target, is_app_mode=True))

    def test_multi_line_and_paragraph_extraction(self):
        raw_input = """First review comment here,

Second review comment with a blank line separator,

Third review comment"""
        items = extract_keyword_list(raw_input)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0], "First review comment here")
        self.assertEqual(items[1], "Second review comment with a blank line separator")
        self.assertEqual(items[2], "Third review comment")

    def test_member_name_matching(self):
        members = "Rahul Sharma\nPriya Verma\nAditya Raj"
        self.assertTrue(match_member_name("Rahul Sharma", members))
        self.assertTrue(match_member_name("rahul sharma", members))
        self.assertTrue(match_member_name("Rahul", members))
        self.assertTrue(match_member_name("Aditya", members))
        self.assertFalse(match_member_name("Vikram Singh", members))


class TestDatabaseLayer(unittest.TestCase):
    """Deep verification of SQLite database, WAL mode, and concurrency."""

    def setUp(self):
        init_db()

    def test_settings_crud(self):
        test_key = "TEST_SUITE_KEY_999"
        set_setting(test_key, "ACTIVE_STATUS")
        val = get_setting(test_key, "DEFAULT")
        self.assertEqual(val, "ACTIVE_STATUS")

    def test_review_deduplication(self):
        import uuid
        uid = uuid.uuid4().hex
        rev = {
            "service_type": "APP",
            "target_id": "com.test.unit",
            "target_name": "Unit Test App",
            "review_id": f"unique_test_rev_{uid}",
            "user_name": "Test User",
            "user_image": "",
            "rating": 5,
            "review_text": "Superb test app review.",
            "review_date": "2026-09-28",
            "review_time": "12:00:00",
            "matched_keywords": "Superb"
        }
        res1 = save_review(rev)
        self.assertTrue(res1)
        # Duplicate insertion should return False and not throw
        res2 = save_review(rev)
        self.assertFalse(res2)

    def test_concurrent_multi_threaded_writes(self):
        """Test WAL mode handling multiple simultaneous writes without lock failure."""
        def worker(thread_id):
            for i in range(10):
                rev = {
                    "service_type": "APP",
                    "target_id": "com.concurrent.test",
                    "target_name": "Concurrency App",
                    "review_id": f"th_{thread_id}_item_{i}_{datetime.now().timestamp()}",
                    "user_name": f"User {thread_id}",
                    "rating": 5,
                    "review_text": "Concurrent write test.",
                    "review_date": "2026-09-28",
                    "review_time": "12:00:00",
                    "matched_keywords": "Concurrent"
                }
                save_review(rev)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, t) for t in range(5)]
            for f in concurrent.futures.as_completed(futures):
                f.result()  # Will raise if any thread suffered locked database error

    def test_campaign_task_lifecycle(self):
        task_id = create_campaign_task(
            service_type="APP",
            target_id="com.campaign.test",
            target_name="Campaign App",
            start_date="2026-09-28",
            check_date="2026-10-06",
            retention_days=8,
            keywords="Fast app",
            members="John Doe",
            bulker_name="Agency A"
        )
        self.assertIsNotNone(task_id)
        task = get_campaign_task_by_id(task_id)
        self.assertEqual(task["target_id"], "com.campaign.test")
        self.assertEqual(task["status"], "PENDING")
        self.assertEqual(task["bulker_name"], "Agency A")
        delete_campaign_task(task_id)
        self.assertIsNone(get_campaign_task_by_id(task_id))


class TestAppFetcherParsing(unittest.TestCase):
    """Deep verification of URL parsing and date formatting."""

    def test_extract_package_id_variants(self):
        url1 = "https://play.google.com/store/apps/details?id=com.whatsapp&hl=en&gl=US"
        url2 = "https://play.google.com/store/apps/details?id=com.effecto.app"
        url3 = "com.spotify.music"
        url4 = "com.instagram.android?referrer=utm_source"

        self.assertEqual(extract_package_id(url1), "com.whatsapp")
        self.assertEqual(extract_package_id(url2), "com.effecto.app")
        self.assertEqual(extract_package_id(url3), "com.spotify.music")
        self.assertEqual(extract_package_id(url4), "com.instagram.android")

    def test_format_review_date(self):
        dt = datetime(2026, 9, 28, 14, 30, 0)
        d_str, t_str = format_review_date(dt)
        self.assertEqual(d_str, "2026-09-28")
        self.assertEqual(t_str, "14:30:00")


class TestBatchAndExport(unittest.TestCase):
    """Deep verification of service detection and CSV exporters."""

    def test_detect_service_type(self):
        self.assertEqual(detect_service_type("https://maps.app.goo.gl/abcdef"), "MAP")
        self.assertEqual(detect_service_type("https://www.google.com/maps/place/Shop"), "MAP")
        self.assertEqual(detect_service_type("com.effecto.app"), "APP")
        self.assertEqual(detect_service_type("https://play.google.com/store/apps/details?id=com.test"), "APP")

    def test_csv_generation(self):
        reviews = [{
            "service_type": "APP",
            "target_id": "com.test",
            "target_name": "Test App",
            "user_name": "Alice",
            "rating": 5,
            "review_text": "Great application, smooth UI.",
            "review_date": "2026-09-28",
            "review_time": "10:00:00",
            "matched_keywords": "smooth UI"
        }]
        csv_str = generate_csv_string(reviews)
        self.assertIn("Reviewer Name", csv_str)
        self.assertIn("Alice", csv_str)
        self.assertIn("smooth UI", csv_str)

        batch_csv = generate_batch_csv_string(reviews)
        self.assertIn("Target Name", batch_csv)
        self.assertIn("Test App", batch_csv)


if __name__ == "__main__":
    print("\n=======================================================")
    print("   RUNNING ARCEUS DEEP FIXATION & VERIFICATION SUITE   ")
    print("=======================================================\n")
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = runner.run(suite)
    if res.wasSuccessful():
        print("\n>>> ALL DEEP TESTS PASSED 100% SUCCESSFULLY! <<<\n")
        sys.exit(0)
    else:
        print("\n>>> TEST SUITE FAILED! <<<")
        sys.exit(1)
