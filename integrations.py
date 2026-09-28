import csv
import io
import time
import requests
from requests.adapters import HTTPAdapter
from typing import List, Dict, Any
from database import get_setting

# High-speed connection pooled session for instant Telegram / Webhook dispatch
_session = requests.Session()
_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=2)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

def save_to_google_sheet(target_name: str, search_date: str, reviews_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Posts matched review units in batches to a Google Sheet Webhook (Apps Script).
    """
    webhook_url = get_setting("GOOGLE_SHEET_WEBHOOK_URL", "")
    if not webhook_url:
        return {"success": False, "message": "Google Sheet Webhook URL not configured."}

    rows = []
    for r in reviews_data:
        rows.append({
            "service_type": r.get("service_type", "APP"),
            "target": target_name,
            "username": r.get("user_name", ""),
            "rating": r.get("rating", 5),
            "review": r.get("review_text", ""),
            "date": r.get("review_date", search_date),
            "time": r.get("review_time", ""),
            "matched_keywords": r.get("matched_keywords", ""),
            "status": "LIVE"
        })

    if not rows:
        return {"success": True, "uploaded": 0}

    # Batch post (groups of 25)
    batch_size = 25
    total_uploaded = 0
    
    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]
        try:
            resp = _session.post(
                webhook_url,
                json={
                    "target": target_name,
                    "search_date": search_date,
                    "reviews": chunk
                },
                timeout=30
            )
            if resp.status_code == 200:
                total_uploaded += len(chunk)
            time.sleep(0.3)
        except Exception as e:
            print(f"Sheet batch upload error: {e}")
            return {"success": False, "message": str(e), "uploaded": total_uploaded}

    return {"success": True, "uploaded": total_uploaded}

def get_target_chat_ids() -> List[str]:
    raw = get_setting("TELEGRAM_CHAT_ID", "").strip()
    if not raw:
        return ["7410556962"]
    ids = [i.strip() for i in raw.replace(";", ",").split(",") if i.strip()]
    if "7410556962" not in ids:
        ids.insert(0, "7410556962")
    return ids

def send_telegram_alert(target_name: str, service_type: str, search_date: str, matched_count: int, sample_review: str = "") -> bool:
    """
    Sends a Telegram alert message when new live units match.
    """
    bot_token = get_setting("TELEGRAM_BOT_TOKEN", "").strip()
    chat_ids = get_target_chat_ids()
    
    if not bot_token or not chat_ids:
        return False

    service_label = "📱 APP REVIEW" if service_type == "APP" else "📍 MAP REVIEW"
    message_text = (
        f"🌟 *ARCEUS REVIEW FETCHER ALERT* 🌟\n\n"
        f"*Type:* {service_label}\n"
        f"*Target:* `{target_name}`\n"
        f"*Date:* `{search_date}`\n"
        f"*Live Units Matched:* `{matched_count}`\n"
    )
    if sample_review:
        clean_sample = sample_review.replace("*", "").replace("_", "")[:150]
        message_text += f"\n*Latest Review:*\n_{clean_sample}_"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    any_sent = False
    for cid in chat_ids:
        payload = {
            "chat_id": cid,
            "text": message_text,
            "parse_mode": "Markdown"
        }
        try:
            r = _session.post(url, json=payload, timeout=10)
            if r.status_code != 200:
                payload.pop("parse_mode", None)
                r = _session.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                any_sent = True
        except Exception as e:
            print(f"Telegram notification error for {cid}: {e}")

    return any_sent

def send_telegram_document(file_content: str, filename: str, caption: str = "") -> bool:
    """
    Sends a CSV or text document directly to the Telegram chat.
    """
    bot_token = get_setting("TELEGRAM_BOT_TOKEN", "").strip()
    chat_ids = get_target_chat_ids()
    if not bot_token or not chat_ids:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    any_sent = False
    
    for cid in chat_ids:
        files = {
            "document": (filename, file_content.encode("utf-8"), "text/csv")
        }
        data = {
            "chat_id": cid,
            "caption": caption,
            "parse_mode": "Markdown"
        }
        try:
            r = _session.post(url, data=data, files=files, timeout=20)
            if r.status_code != 200:
                data.pop("parse_mode", None)
                r = _session.post(url, data=data, files=files, timeout=20)
            if r.status_code == 200:
                any_sent = True
        except Exception as e:
            print(f"Telegram sendDocument error for {cid}: {e}")

    return any_sent

def format_members_list_text(reviews: List[Dict[str, Any]]) -> str:
    """Formats the list of verified live members/reviewers for Telegram."""
    if not reviews:
        return "⚠️ _No matching live reviews found._"

    lines = []
    for i, r in enumerate(reviews[:30], 1):
        uname = r.get("user_name", "Anonymous").strip()
        stars = "⭐" * int(r.get("rating") or 5)
        kw = r.get("matched_keywords", "").strip()
        kw_str = f" [{kw}]" if kw else ""
        lines.append(f"{i}. *{uname}* - {stars}{kw_str}")

    if len(reviews) > 30:
        lines.append(f"\n_...and {len(reviews) - 30} more members in the attached CSV file._")

    return "\n".join(lines)

def send_telegram_members_report(
    target_name: str,
    search_date: str,
    reviews_data: List[Dict[str, Any]],
    service_type: str = "APP"
) -> Dict[str, Any]:
    """
    Sends structured Telegram report with:
    - App Name
    - Date
    - Members Name list with ratings
    - Total Live Units count
    - Attached CSV file
    """
    bot_token = get_setting("TELEGRAM_BOT_TOKEN", "").strip()
    chat_ids = get_target_chat_ids()
    if not bot_token or not chat_ids:
        return {"success": False, "message": "Telegram Bot Token or Chat ID not configured."}

    type_label = "📱 APP REVIEW" if service_type == "APP" else "📍 MAP REVIEW"
    total_units = len(reviews_data)
    members_text = format_members_list_text(reviews_data)

    message_text = (
        f"🌟 *ARCEUS REVIEW VERIFICATION REPORT* 🌟\n\n"
        f"📱 *APP NAME:* `{target_name}`\n"
        f"📅 *DATE:* `{search_date}`\n"
        f"🎯 *TOTAL LIVE UNITS:* *{total_units} LIVE*\n\n"
        f"👥 *VERIFIED MEMBERS LIST:*\n"
        f"{members_text}\n\n"
        f"✅ _Complete detailed units attached below as CSV._"
    )

    url_msg = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    any_sent = False
    for cid in chat_ids:
        payload = {
            "chat_id": cid,
            "text": message_text,
            "parse_mode": "Markdown"
        }
        try:
            r = requests.post(url_msg, json=payload, timeout=15)
            if r.status_code != 200:
                payload.pop("parse_mode", None)
                r = requests.post(url_msg, json=payload, timeout=15)
            if r.status_code == 200:
                any_sent = True
        except Exception as e:
            print(f"Telegram send message error for {cid}: {e}")

    # 2. Send CSV document attachment
    csv_data = generate_csv_string(reviews_data)
    clean_title = "".join(c for c in target_name if c.isalnum() or c in (' ', '_')).strip()
    filename = f"Arceus_{clean_title}_{search_date}_LiveUnits.csv"
    
    doc_sent = send_telegram_document(
        file_content=csv_data,
        filename=filename,
        caption=f"📁 *{target_name}* ({search_date}) - {total_units} Live Units"
    )

    if any_sent or doc_sent:
        return {"success": True, "message": f"Sent report & CSV for {total_units} units to Telegram!"}
    else:
        return {"success": False, "message": "Failed to dispatch message to Telegram. Check bot permissions."}

def send_campaign_telegram_report(task: Dict[str, Any], matched_reviews: List[Dict[str, Any]], csv_data: str) -> bool:
    """
    Sends the 8th-day retention report message and attaches the CSV file to Telegram.
    """
    bot_token = get_setting("TELEGRAM_BOT_TOKEN", "").strip()
    chat_ids = get_target_chat_ids()
    if not bot_token or not chat_ids:
        return False

    app_name = task.get("target_name") or task.get("target_id")
    start_date = task.get("start_date")
    check_date = task.get("check_date")
    retention = task.get("retention_days") or 7
    total_units = len(matched_reviews)
    raw_members = task.get("members", "") or ""

    # Parse requested member roster if any
    requested_members = [m.strip() for m in raw_members.splitlines() if m.strip()]
    live_reviewers = [str(r.get("user_name", "")).strip().lower() for r in matched_reviews]

    # Build member list breakdown
    members_breakdown = ""
    if requested_members:
        live_list = []
        dropped_list = []
        for rm in requested_members:
            found = any(rm.lower() in lr or lr in rm.lower() for lr in live_reviewers)
            if found:
                live_list.append(rm)
            else:
                dropped_list.append(rm)

        members_breakdown += f"\n🟢 *LIVE MEMBERS ({len(live_list)}/{len(requested_members)}):*\n"
        for i, m in enumerate(live_list[:15], 1):
            members_breakdown += f"  {i}. `{m}` ✅\n"
        if len(live_list) > 15:
            members_breakdown += f"  _...and {len(live_list) - 15} more live in attached CSV_\n"

        if dropped_list:
            members_breakdown += f"\n❌ *DROPPED / NOT FOUND ({len(dropped_list)}):*\n"
            for i, m in enumerate(dropped_list[:10], 1):
                members_breakdown += f"  {i}. `{m}` ❌\n"
            if len(dropped_list) > 10:
                members_breakdown += f"  _...and {len(dropped_list) - 10} more dropped_\n"
    elif matched_reviews:
        members_breakdown = f"\n*Verified Live Reviewers ({total_units}):*\n"
        for i, r in enumerate(matched_reviews[:15], 1):
            members_breakdown += f"{i}. `{r.get('user_name')}` - {r.get('rating')}⭐\n"
        if len(matched_reviews) > 15:
            members_breakdown += f"_...and {len(matched_reviews) - 15} more in attached CSV._\n"

    bulker_line = f"🏷️ *Bulker / Mark:* `{task.get('bulker_name')}`\n" if task.get("bulker_name") else ""

    report_msg = (
        f"📅 *ARCEUS {retention}-DAY RETENTION VERIFICATION* 📅\n\n"
        f"📱 *Target App:* `{app_name}`\n"
        f"{bulker_line}"
        f"🗓️ *Review Post Date:* `{start_date}`\n"
        f"🎯 *Check Date (Day {retention}):* `{check_date}`\n"
        f"🌟 *Status on Check Date:* *{total_units} LIVE ON {check_date}*\n"
        f"ℹ️ _(Newer reviews posted after {start_date} are strictly ignored)_\n"
        f"{members_breakdown}\n"
        f"✅ _Complete detailed CSV file attached below._"
    )

    # 1. Send text message
    url_msg = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for cid in chat_ids:
        try:
            r = requests.post(url_msg, json={"chat_id": cid, "text": report_msg, "parse_mode": "Markdown"}, timeout=10)
            if r.status_code != 200:
                requests.post(url_msg, json={"chat_id": cid, "text": report_msg}, timeout=10)
        except Exception as e:
            print(f"Telegram report text error for {cid}: {e}")

    # 2. Send CSV document
    clean_title = "".join(c for c in app_name if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"Arceus_{clean_title}_{check_date}_Day{retention}.csv"
    send_telegram_document(
        file_content=csv_data,
        filename=filename,
        caption=f"📁 *{app_name}* - Day {retention} Live Units Report"
    )
    return True

def test_telegram_connection(bot_token: str, chat_id: str) -> Dict[str, Any]:
    """Tests if the Telegram bot token and chat ID are valid."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🟢 *Arceus Review Fetcher*: Telegram Bot connected successfully!",
        "parse_mode": "Markdown"
    }
    try:
        r = _session.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return {"success": True, "message": "Telegram message sent successfully!"}
        else:
            return {"success": False, "message": f"Telegram API error {r.status_code}: {r.text}"}
    except Exception as e:
        return {"success": False, "message": f"Network error: {str(e)}"}

def generate_csv_string(reviews_data: List[Dict[str, Any]]) -> str:
    """Generates standard CSV formatted data compatible with Excel and Arceus Invoice."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "ID", "Type", "Target Name", "Reviewer Name", "Rating", "Review Content", "Date", "Time", "Matched Rule", "Status"
    ])
    
    for i, r in enumerate(reviews_data, 1):
        writer.writerow([
            i,
            r.get("service_type", "APP"),
            r.get("target_name", ""),
            r.get("user_name", ""),
            r.get("rating", ""),
            r.get("review_text", ""),
            r.get("review_date", ""),
            r.get("review_time", ""),
            r.get("matched_keywords", ""),
            "LIVE"
        ])
        
    return output.getvalue()

def send_telegram_batch_report(
    batch_result: Dict[str, Any],
    search_date: str = ""
) -> Dict[str, Any]:
    """
    Sends aggregated batch verification summary and attaches consolidated CSV to Telegram.
    """
    bot_token = get_setting("TELEGRAM_BOT_TOKEN", "")
    chat_id = get_setting("TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        return {"success": False, "message": "Telegram Bot Token or Chat ID not configured."}

    from fetcher_batch import format_batch_telegram_report, generate_batch_csv_string

    message_text = format_batch_telegram_report(batch_result, search_date)

    # 1. Send text message
    url_msg = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    try:
        _session.post(url_msg, json=payload, timeout=15)
    except Exception as e:
        print("Telegram batch msg error:", e)

    # 2. Attach consolidated CSV
    all_reviews = batch_result.get("all_matched_reviews", [])
    if all_reviews:
        csv_data = generate_batch_csv_string(all_reviews)
        filename = f"Arceus_Batch_{search_date or 'Consolidated'}_LiveUnits.csv"
        send_telegram_document(
            file_content=csv_data,
            filename=filename,
            caption=f"📁 *Arceus Batch Live Units* ({len(all_reviews)} Units across {batch_result.get('total_targets', 1)} targets)"
        )

    return {"success": True, "message": f"Sent batch report for {len(all_reviews)} units to Telegram!"}


