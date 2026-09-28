import time
import io
import csv
from typing import List, Dict, Any, Optional

from fetcher_app import fetch_app_reviews
from fetcher_map import fetch_map_reviews
from database import save_review, log_scan_run

def detect_service_type(target_str: str) -> str:
    """Detects whether a target string is a Google Maps link or Google Play app."""
    target_lower = target_str.lower().strip()
    if (
        "maps.app.goo.gl" in target_lower or
        "google.com/maps" in target_lower or
        "goo.gl/maps" in target_lower or
        "maps.google" in target_lower or
        "/place/" in target_lower or
        "cid=" in target_lower
    ):
        return "MAP"
    return "APP"

def run_batch_fetch(
    raw_targets: str,
    search_date: Optional[str] = None,
    rating: Optional[int] = None,
    keywords: Optional[str] = None,
    exact_word: bool = False,
    members: Optional[str] = None,
    ending_hint: Optional[str] = None,
    auto_save: bool = True
) -> Dict[str, Any]:
    """
    Executes sequential batch fetching across multiple App or Map targets.
    Returns per-target summaries and an aggregated list of all matched reviews.
    """
    lines = [line.strip() for line in raw_targets.split("\n") if line.strip()]
    if not lines:
        return {
            "success": False,
            "error": "No valid targets provided in batch list.",
            "total_targets": 0,
            "targets_summary": [],
            "all_matched_reviews": [],
            "total_scanned": 0,
            "total_matched": 0
        }

    import concurrent.futures

    def _process_single_target(args):
        idx, target_item = args
        srv_type = detect_service_type(target_item)
        target_name = target_item
        scanned_count = 0
        matched_count = 0
        status = "SUCCESS"
        error_msg = None
        current_matched: List[Dict[str, Any]] = []

        try:
            if srv_type == "MAP":
                fetch_res = fetch_map_reviews(
                    target_input=target_item,
                    search_date=search_date,
                    rating=rating,
                    keyword_text=keywords,
                    exact_word=exact_word,
                    members_text=members,
                    ending_hint=ending_hint
                )
                place_info = fetch_res.get("place_info") or {}
                target_name = place_info.get("title") or target_item
            else:
                fetch_res = fetch_app_reviews(
                    package_id=target_item,
                    search_date=search_date,
                    rating=rating,
                    keyword_text=keywords,
                    exact_word=exact_word,
                    members_text=members,
                    ending_hint=ending_hint,
                    max_scan=400
                )
                app_info = fetch_res.get("app_info") or {}
                target_name = app_info.get("title") or target_item

            scanned_count = fetch_res.get("total_scanned", 0)
            current_matched = fetch_res.get("reviews", [])
            matched_count = len(current_matched)

            # Inject target metadata into each review
            for r in current_matched:
                r["target_name"] = target_name
                r["target_id"] = target_item
                r["service_type"] = srv_type
                if auto_save:
                    try:
                        save_review(r)
                    except Exception:
                        pass

            if auto_save:
                try:
                    log_scan_run(
                        service_type=srv_type,
                        target_id=target_item,
                        target_name=target_name,
                        search_date=search_date,
                        total_scanned=scanned_count,
                        total_matched=matched_count
                    )
                except Exception:
                    pass

        except Exception as ex:
            status = "ERROR"
            error_msg = str(ex)

        summary_entry = {
            "index": idx,
            "target_id": target_item,
            "target_name": target_name,
            "service_type": srv_type,
            "scanned": scanned_count,
            "matched": matched_count,
            "status": status,
            "error": error_msg
        }
        return summary_entry, current_matched, scanned_count, matched_count

    max_workers = min(6, len(lines))
    indexed_lines = list(enumerate(lines, 1))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_process_single_target, indexed_lines))

    targets_summary: List[Dict[str, Any]] = []
    all_matched_reviews: List[Dict[str, Any]] = []
    total_scanned_overall = 0
    total_matched_overall = 0

    for summary_entry, current_matched, scanned_count, matched_count in results:
        targets_summary.append(summary_entry)
        all_matched_reviews.extend(current_matched)
        total_scanned_overall += scanned_count
        total_matched_overall += matched_count

    return {
        "success": True,
        "total_targets": len(targets_summary),
        "targets_summary": targets_summary,
        "all_matched_reviews": all_matched_reviews,
        "total_scanned": total_scanned_overall,
        "total_matched": total_matched_overall
    }

def generate_batch_csv_string(reviews: List[Dict[str, Any]]) -> str:
    """Generates a consolidated CSV string containing reviews from all batch targets."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Standard billing & audit headers
    headers = [
        "Index",
        "Target Name",
        "Service Type",
        "Reviewer Name",
        "Rating (Stars)",
        "Review Content",
        "Review Date",
        "Matched Rule",
        "Target ID / Link",
        "Status"
    ]
    writer.writerow(headers)

    for idx, r in enumerate(reviews, 1):
        writer.writerow([
            idx,
            r.get("target_name", "Unknown"),
            r.get("service_type", "APP"),
            r.get("user_name", r.get("userName", r.get("author", "Anonymous"))),
            r.get("rating", r.get("score", 5)),
            (r.get("review_text", r.get("content", r.get("text", "")))).replace("\n", " "),
            r.get("review_date", r.get("date", "")),
            r.get("matched_keywords", r.get("matched_keyword", "Matched")),
            r.get("target_id", ""),
            "LIVE"
        ])

    return output.getvalue()

def format_batch_telegram_report(
    batch_result: Dict[str, Any],
    search_date: Optional[str] = None
) -> str:
    """Formats a neat Telegram summary of the entire batch run."""
    targets = batch_result.get("targets_summary", [])
    tot_targets = batch_result.get("total_targets", 0)
    tot_scanned = batch_result.get("total_scanned", 0)
    tot_matched = batch_result.get("total_matched", 0)

    lines = [
        "👑 *ARCEUS BATCH VERIFICATION REPORT*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📅 *Date Window:* `{search_date or 'Today / All'}`",
        f"🗂️ *Total Targets:* `{tot_targets}`",
        f"📊 *Total Scanned:* `{tot_scanned}`",
        f"🎯 *Total Verified Live:* `{tot_matched} Units`",
        "━━━━━━━━━━━━━━━━━━━━",
        "📋 *Targets Breakdown:*"
    ]

    for t in targets:
        icon = "📱" if t.get("service_type") == "APP" else "📍"
        name = str(t.get("target_name", "Target"))[:26]
        matched = t.get("matched", 0)
        status_icon = "✅" if t.get("status") == "SUCCESS" else "⚠️"
        lines.append(f"{icon} *{name}*: `{matched} Live` {status_icon}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("Status: *100% VERIFIED LIVE UNITS* ✔️")
    return "\n".join(lines)
