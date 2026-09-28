from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from typing import Dict, Any, Optional
from fetcher_app import fetch_app_reviews
from fetcher_map import fetch_map_reviews
from database import save_review, log_scan_run
from integrations import save_to_google_sheet, send_telegram_alert

# Global scheduler instance
scheduler = BackgroundScheduler()
scheduler.start()

# State holder for active auto-fetch task
active_autofetch_job = {
    "is_running": False,
    "job_id": None,
    "service_type": "APP",
    "target_id": "",
    "interval_minutes": 5,
    "search_date": "",
    "last_run": None,
    "matched_count": 0,
    "total_scanned": 0
}

def run_autofetch_cycle(params: Dict[str, Any]):
    """Executes a single cycle of the auto-fetch monitor."""
    service_type = params.get("service_type", "APP")
    target_id = params.get("target_id", "")
    search_date = params.get("search_date", datetime.now().strftime("%Y-%m-%d"))
    rating = params.get("rating")
    keywords = params.get("keywords", "")
    exact_word = params.get("exact_word", False)
    members = params.get("members", "")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-Fetch running for {service_type}: {target_id}")

    if service_type == "APP":
        res = fetch_app_reviews(
            package_id=target_id,
            search_date=search_date,
            rating=rating,
            keyword_text=keywords,
            exact_word=exact_word,
            members_text=members
        )
    else:
        res = fetch_map_reviews(
            target_input=target_id,
            search_date=search_date,
            rating=rating,
            keyword_text=keywords,
            exact_word=exact_word,
            members_text=members
        )

    matched = res.get("reviews", [])
    new_units = 0

    # Save to SQLite and count newly discovered reviews
    for r in matched:
        if save_review(r):
            new_units += 1

    active_autofetch_job["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    active_autofetch_job["total_scanned"] = res.get("total_scanned", 0)
    active_autofetch_job["matched_count"] = len(matched)

    log_scan_run(
        service_type=service_type,
        target_id=target_id,
        search_date=search_date,
        total_scanned=res.get("total_scanned", 0),
        total_matched=len(matched),
        run_type="AUTO"
    )

    # If new live units were found in this cycle, notify and upload
    if new_units > 0:
        print(f"🎉 Auto-Fetch detected {new_units} NEW live review units!")
        save_to_google_sheet(
            target_name=res.get("app_info", {}).get("title") or target_id,
            search_date=search_date,
            reviews_data=matched
        )
        sample = matched[0].get("review_text", "") if matched else ""
        send_telegram_alert(
            target_name=res.get("app_info", {}).get("title") or target_id,
            service_type=service_type,
            search_date=search_date,
            matched_count=len(matched),
            sample_review=sample
        )

def start_autofetch(params: Dict[str, Any]) -> Dict[str, Any]:
    """Starts background scheduled auto-fetch."""
    stop_autofetch()

    interval = int(params.get("interval_minutes", 5))
    job_id = f"autofetch_{int(datetime.now().timestamp())}"

    # Schedule recurring job
    scheduler.add_job(
        func=run_autofetch_cycle,
        trigger="interval",
        minutes=interval,
        id=job_id,
        args=[params],
        replace_existing=True
    )

    # Immediately run first iteration
    scheduler.add_job(
        func=run_autofetch_cycle,
        args=[params]
    )

    active_autofetch_job.update({
        "is_running": True,
        "job_id": job_id,
        "service_type": params.get("service_type", "APP"),
        "target_id": params.get("target_id", ""),
        "interval_minutes": interval,
        "search_date": params.get("search_date", datetime.now().strftime("%Y-%m-%d")),
        "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return {"success": True, "job": active_autofetch_job}

def stop_autofetch() -> Dict[str, Any]:
    """Stops the active background auto-fetch job."""
    if active_autofetch_job.get("is_running") and active_autofetch_job.get("job_id"):
        try:
            scheduler.remove_job(active_autofetch_job["job_id"])
        except Exception:
            pass
    active_autofetch_job["is_running"] = False
    active_autofetch_job["job_id"] = None
    return {"success": True, "message": "Auto-fetch monitor stopped."}

def get_autofetch_status() -> Dict[str, Any]:
    return active_autofetch_job

# =======================================================
# 8-DAY RETENTION AUTO-CAMPAIGN RUNNER
# =======================================================

def execute_campaign_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a scheduled retention check task, saves reviews, and dispatches Telegram report with CSV.
    """
    task_id = task["id"]
    service_type = task.get("service_type", "APP")
    target_id = task.get("target_id", "")
    start_date = task.get("start_date", "")
    keywords = task.get("keywords", "")
    members = task.get("members", "")

    print(f"[CAMPAIGN] Running 8-Day Retention Check for Task #{task_id} ({target_id})...")

    if service_type == "APP":
        res = fetch_app_reviews(
            package_id=target_id,
            search_date=start_date, # check reviews from list date
            rating=None,            # all stars or matching rule
            keyword_text=keywords,
            exact_word=False,
            members_text=members,
            max_scan=1500
        )
    else:
        res = fetch_map_reviews(
            target_input=target_id,
            search_date=start_date,
            rating=None,
            keyword_text=keywords,
            exact_word=False,
            members_text=members
        )

    matched = res.get("reviews", [])
    
    # Save all matched reviews to database
    for r in matched:
        save_review(r)

    # Generate CSV document
    from integrations import generate_csv_string, send_campaign_telegram_report
    csv_data = generate_csv_string(matched)

    # Send to Telegram Bot
    from database import update_campaign_task_status
    tg_sent = send_campaign_telegram_report(task, matched, csv_data)

    # Update task in database
    update_campaign_task_status(
        task_id=task_id,
        status="COMPLETED",
        matched_units=len(matched),
        telegram_sent=1 if tg_sent else 0
    )

    print(f"[CAMPAIGN] Retention task #{task_id} completed: {len(matched)} live units. Telegram dispatched: {tg_sent}")
    return {
        "success": True,
        "task_id": task_id,
        "matched_units": len(matched),
        "telegram_sent": tg_sent,
        "reviews": matched
    }

def check_daily_retention_campaigns():
    """
    Periodic job: runs every hour to see if today is the 8th day for any scheduled campaign.
    """
    from database import get_due_campaign_tasks
    today_str = datetime.now().strftime("%Y-%m-%d")
    due_tasks = get_due_campaign_tasks(today_str)

    if due_tasks:
        print(f"[CAMPAIGN] Found {len(due_tasks)} retention campaign(s) due for 8th-day check today ({today_str})!")
        for t in due_tasks:
            try:
                execute_campaign_task(t)
            except Exception as e:
                print(f"Error executing campaign task #{t.get('id')}: {e}")

# Register recurring retention checker to run hourly
scheduler.add_job(
    func=check_daily_retention_campaigns,
    trigger="interval",
    hours=1,
    id="retention_campaign_hourly_checker",
    misfire_grace_time=3600,
    replace_existing=True
)

# Run a check on server start as well
scheduler.add_job(
    func=check_daily_retention_campaigns,
    id="retention_campaign_startup_check",
    misfire_grace_time=3600
)

