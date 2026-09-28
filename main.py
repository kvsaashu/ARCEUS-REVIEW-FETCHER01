import os
import asyncio
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, Form, Response, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from config import HOST, PORT, BASE_DIR
from fetcher_app import fetch_app_reviews
from fetcher_map import fetch_map_reviews
from matcher import match_keywords
from database import (
    save_review, log_scan_run, get_recent_reviews, get_setting, set_setting,
    create_campaign_task, get_campaign_tasks, get_campaign_task_by_id, delete_campaign_task
)
from scheduler import start_autofetch, stop_autofetch, get_autofetch_status, execute_campaign_task
from integrations import (
    save_to_google_sheet, send_telegram_alert, generate_csv_string, test_telegram_connection,
    send_telegram_batch_report
)
from fetcher_batch import run_batch_fetch, generate_batch_csv_string
from tunnel_manager import tunnel_mgr

from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(title="Arceus Review Fetcher")

# High-performance GZip compression for mobile & web speed
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prevent browser from serving stale cached JS/CSS files
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Setup directories
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Pydantic schemas for API requests
class FetchRequest(BaseModel):
    service_type: str = "APP"             # "APP" or "MAP"
    target_id: str                         # Package ID or Maps URL
    search_date: Optional[str] = None
    rating: Optional[int] = None
    keywords: Optional[str] = None
    exact_word: bool = False
    members: Optional[str] = None
    ending_hint: Optional[str] = None
    auto_save: bool = True

class BatchFetchRequest(BaseModel):
    targets: str                          # Multi-line target IDs / URLs
    search_date: Optional[str] = None
    rating: Optional[int] = None
    keywords: Optional[str] = None
    exact_word: bool = False
    members: Optional[str] = None
    ending_hint: Optional[str] = None
    auto_save: bool = True

class BatchTelegramRequest(BaseModel):
    batch_result: Dict[str, Any]
    search_date: Optional[str] = ""

class AutoFetchStartRequest(BaseModel):
    service_type: str = "APP"
    target_id: str
    search_date: Optional[str] = None
    rating: Optional[int] = None
    keywords: Optional[str] = None
    exact_word: bool = False
    members: Optional[str] = None
    ending_hint: Optional[str] = None
    interval_minutes: int = 5

class SettingsUpdateRequest(BaseModel):
    google_sheet_webhook_url: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    google_places_api_key: Optional[str] = None
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None
    security_pin: Optional[str] = None
    lock_settings_enabled: Optional[bool] = True
    lock_campaigns_enabled: Optional[bool] = None
    lock_tunnel_enabled: Optional[bool] = None
    remove_pin: Optional[bool] = False

class VerifyPinRequest(BaseModel):
    pin: str

class VerifyAdminAuthRequest(BaseModel):
    username: str
    password: str


@app.get("/healthz")
@app.get("/health")
async def healthz():
    return {"status": "healthy", "service": "Arceus Review Fetcher"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    settings = {
        "sheet_webhook": get_setting("GOOGLE_SHEET_WEBHOOK_URL", ""),
        "tg_token": get_setting("TELEGRAM_BOT_TOKEN", ""),
        "tg_chat": get_setting("TELEGRAM_CHAT_ID", ""),
        "places_key": get_setting("GOOGLE_PLACES_API_KEY", "")
    }
    autofetch_state = get_autofetch_status()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "settings": settings,
            "autofetch": autofetch_state
        }
    )

@app.post("/api/fetch")
async def api_fetch(req: FetchRequest):
    """Manual on-demand review fetch endpoint."""
    if not req.target_id.strip():
        return JSONResponse({"success": False, "error": "Target ID or URL cannot be empty."}, status_code=400)

    if req.service_type == "APP":
        result = await asyncio.to_thread(
            fetch_app_reviews,
            package_id=req.target_id,
            search_date=req.search_date,
            rating=req.rating,
            keyword_text=req.keywords,
            exact_word=req.exact_word,
            members_text=req.members,
            ending_hint=req.ending_hint
        )
    else:
        result = await asyncio.to_thread(
            fetch_map_reviews,
            target_input=req.target_id,
            search_date=req.search_date,
            rating=req.rating,
            keyword_text=req.keywords,
            exact_word=req.exact_word,
            members_text=req.members,
            ending_hint=req.ending_hint
        )

    # Save to SQLite database
    matched_reviews = result.get("reviews", [])
    new_units = 0
    if req.auto_save:
        for r in matched_reviews:
            if save_review(r):
                new_units += 1

        log_scan_run(
            service_type=req.service_type,
            target_id=req.target_id,
            search_date=req.search_date or "",
            total_scanned=result.get("total_scanned", 0),
            total_matched=len(matched_reviews),
            run_type="MANUAL"
        )

    result["new_units"] = new_units
    return result

@app.post("/api/autofetch/start")
async def api_start_autofetch(req: AutoFetchStartRequest):
    if not req.target_id.strip():
        return JSONResponse({"success": False, "error": "Target ID cannot be empty."}, status_code=400)

    res = start_autofetch(req.model_dump())
    return res

@app.post("/api/autofetch/stop")
async def api_stop_autofetch():
    return stop_autofetch()

@app.get("/api/autofetch/status")
async def api_autofetch_status():
    return get_autofetch_status()

@app.post("/api/export/csv")
async def api_export_csv(reviews: List[Dict[str, Any]]):
    """Generates a downloadable CSV file."""
    csv_data = generate_csv_string(reviews)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=arceus_reviews_matched.csv"}
    )

@app.post("/api/sync/sheet")
async def api_sync_sheet(data: Dict[str, Any]):
    target_name = data.get("target_name", "App Review")
    search_date = data.get("search_date", "")
    reviews_list = data.get("reviews", [])
    res = save_to_google_sheet(target_name, search_date, reviews_list)
    return res

@app.get("/api/settings")
async def api_get_settings():
    stored_pin = get_setting("SECURITY_PIN", "")
    admin_user = get_setting("ADMIN_USERNAME", "admin")
    return {
        "google_sheet_webhook_url": get_setting("GOOGLE_SHEET_WEBHOOK_URL", ""),
        "telegram_bot_token": get_setting("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": get_setting("TELEGRAM_CHAT_ID", ""),
        "google_places_api_key": get_setting("GOOGLE_PLACES_API_KEY", ""),
        "admin_username": admin_user,
        "has_security_pin": bool(stored_pin),
        "lock_settings_enabled": get_setting("LOCK_SETTINGS_ENABLED", "true") == "true",
        "lock_campaigns_enabled": get_setting("LOCK_CAMPAIGNS_ENABLED", "false") == "true",
        "lock_tunnel_enabled": get_setting("LOCK_TUNNEL_ENABLED", "false") == "true"
    }

@app.post("/api/settings")
async def api_save_settings(req: SettingsUpdateRequest):
    if req.google_sheet_webhook_url is not None:
        set_setting("GOOGLE_SHEET_WEBHOOK_URL", req.google_sheet_webhook_url.strip())
    if req.telegram_bot_token is not None:
        set_setting("TELEGRAM_BOT_TOKEN", req.telegram_bot_token.strip())
    if req.telegram_chat_id is not None:
        set_setting("TELEGRAM_CHAT_ID", req.telegram_chat_id.strip())
    if req.google_places_api_key is not None:
        set_setting("GOOGLE_PLACES_API_KEY", req.google_places_api_key.strip())
    
    # Admin Credentials (ID & Password)
    if req.admin_username is not None and req.admin_username.strip():
        set_setting("ADMIN_USERNAME", req.admin_username.strip())
    if req.admin_password is not None and req.admin_password.strip():
        set_setting("ADMIN_PASSWORD", req.admin_password.strip())

    # Security Locks
    if req.remove_pin:
        set_setting("SECURITY_PIN", "")
        set_setting("LOCK_SETTINGS_ENABLED", "false")
        set_setting("LOCK_CAMPAIGNS_ENABLED", "false")
        set_setting("LOCK_TUNNEL_ENABLED", "false")
    else:
        if req.security_pin is not None and req.security_pin.strip():
            set_setting("SECURITY_PIN", req.security_pin.strip())
        if req.lock_settings_enabled is not None:
            set_setting("LOCK_SETTINGS_ENABLED", "true" if req.lock_settings_enabled else "false")
        if req.lock_campaigns_enabled is not None:
            set_setting("LOCK_CAMPAIGNS_ENABLED", "true" if req.lock_campaigns_enabled else "false")
        if req.lock_tunnel_enabled is not None:
            set_setting("LOCK_TUNNEL_ENABLED", "true" if req.lock_tunnel_enabled else "false")

    return {"success": True, "message": "Settings & Security Credentials updated successfully."}

@app.post("/api/settings/verify_auth")
async def api_verify_auth(req: VerifyAdminAuthRequest):
    stored_user = get_setting("ADMIN_USERNAME", "admin").strip()
    stored_pass = get_setting("ADMIN_PASSWORD", "admin").strip()
    locked = get_setting("LOCK_SETTINGS_ENABLED", "true") == "true"
    
    if not locked:
        return {"success": True, "locked": False, "valid": True}
    
    is_user_match = req.username.strip().lower() == stored_user.lower()
    is_pass_match = req.password.strip() == stored_pass
    
    if is_user_match and is_pass_match:
        return {"success": True, "locked": True, "valid": True, "username": stored_user}
    else:
        return {"success": False, "locked": True, "valid": False, "error": "Invalid Admin ID or Password"}

@app.post("/api/settings/verify_pin")
async def api_verify_pin(req: VerifyPinRequest):
    stored_pin = get_setting("SECURITY_PIN", "")
    stored_pass = get_setting("ADMIN_PASSWORD", "admin")
    if not stored_pin:
        # Check against admin password if no PIN explicitly set
        valid = (req.pin.strip() == stored_pass.strip())
        return {"success": True, "locked": False, "valid": valid}
    valid = (req.pin.strip() == stored_pin.strip() or req.pin.strip() == stored_pass.strip())
    return {"success": True, "locked": True, "valid": valid}


# --- BATCH FETCHING ENDPOINTS ---

@app.post("/api/batch_fetch")
async def api_batch_fetch(req: BatchFetchRequest):
    if not req.targets.strip():
        return JSONResponse({"success": False, "error": "Target list cannot be empty."}, status_code=400)
    res = await asyncio.to_thread(
        run_batch_fetch,
        raw_targets=req.targets,
        search_date=req.search_date,
        rating=req.rating,
        keywords=req.keywords,
        exact_word=req.exact_word,
        members=req.members,
        ending_hint=req.ending_hint,
        auto_save=req.auto_save
    )
    return res

@app.post("/api/batch_export_csv")
async def api_batch_export_csv(reviews: List[Dict[str, Any]]):
    """Generates a consolidated downloadable CSV for all matched batch reviews."""
    import time
    csv_data = generate_batch_csv_string(reviews)
    filename = f"Arceus_Batch_Matched_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/batch_telegram_alert")
async def api_batch_telegram_alert(req: BatchTelegramRequest):
    res = send_telegram_batch_report(req.batch_result, req.search_date or "")
    return res

# --- CLOUDFLARE REMOTE TUNNEL ENDPOINTS ---

@app.post("/api/tunnel/start")
async def api_tunnel_start():
    res = tunnel_mgr.start_tunnel()
    return res

@app.post("/api/tunnel/stop")
async def api_tunnel_stop():
    res = tunnel_mgr.stop_tunnel()
    return res

@app.get("/api/tunnel/status")
async def api_tunnel_status():
    res = tunnel_mgr.get_status()
    return res

class CampaignCreateRequest(BaseModel):
    service_type: str = "APP"
    target_id: str
    target_name: Optional[str] = ""
    start_date: str
    check_date: Optional[str] = None
    retention_days: Optional[int] = 8
    keywords: Optional[str] = ""
    members: Optional[str] = ""
    ending_hint: Optional[str] = ""
    bulker_name: Optional[str] = ""

class TelegramTestRequest(BaseModel):
    bot_token: str
    chat_id: str

# --- CAMPAIGN MANAGEMENT ENDPOINTS ---

@app.get("/api/campaigns")
async def api_get_campaigns():
    tasks = get_campaign_tasks()
    from datetime import datetime
    today = datetime.now().date()
    
    # Calculate days remaining for each task
    for t in tasks:
        try:
            chk = datetime.strptime(t["check_date"], "%Y-%m-%d").date()
            diff = (chk - today).days
            t["days_remaining"] = diff
        except Exception:
            t["days_remaining"] = 0
            
    return {"success": True, "campaigns": tasks}

@app.post("/api/campaigns")
async def api_create_campaign(req: CampaignCreateRequest):
    if not req.target_id.strip():
        return JSONResponse({"success": False, "error": "Target ID cannot be empty."}, status_code=400)

    from datetime import datetime, timedelta
    try:
        dt_start = datetime.strptime(req.start_date, "%Y-%m-%d")
    except Exception:
        dt_start = datetime.now()
    
    # Check if a custom check_date was provided
    if req.check_date and req.check_date.strip():
        check_date_str = req.check_date.strip()
        try:
            d_start = dt_start.date()
            d_check = datetime.strptime(check_date_str, "%Y-%m-%d").date()
            retention = (d_check - d_start).days + 1
            if retention < 1:
                retention = 1
        except Exception:
            retention = req.retention_days or 8
    else:
        retention = req.retention_days or 8
        dt_check = dt_start + timedelta(days=(retention - 1))
        check_date_str = dt_check.strftime("%Y-%m-%d")

    target_name = req.target_name.strip() if req.target_name else req.target_id
    if req.service_type == "APP" and not req.target_name:
        from fetcher_app import get_app_info, extract_package_id
        info = get_app_info(extract_package_id(req.target_id))
        target_name = info.get("title") or req.target_id

    task_id = create_campaign_task(
        service_type=req.service_type,
        target_id=req.target_id.strip(),
        target_name=target_name,
        start_date=req.start_date,
        check_date=check_date_str,
        retention_days=retention,
        keywords=req.keywords or "",
        members=req.members or "",
        bulker_name=(req.bulker_name or "").strip()
    )

    return {
        "success": True,
        "task_id": task_id,
        "target_name": target_name,
        "check_date": check_date_str,
        "message": f"Task scheduled! Will automatically verify on {check_date_str} (Day {retention}) and send to Telegram."
    }

@app.post("/api/campaigns/{task_id}/check_now")
async def api_run_campaign_now(task_id: int):
    task = get_campaign_task_by_id(task_id)
    if not task:
        return JSONResponse({"success": False, "error": "Campaign task not found."}, status_code=404)

    res = execute_campaign_task(task)
    return res

@app.delete("/api/campaigns/{task_id}")
async def api_delete_campaign(task_id: int):
    success = delete_campaign_task(task_id)
    return {"success": success}

class TelegramAlertRequest(BaseModel):
    app_name: str
    search_date: str
    service_type: str = "APP"
    reviews: List[Dict[str, Any]]

@app.post("/api/telegram/send_alert")
async def api_telegram_send_alert(req: TelegramAlertRequest):
    from integrations import send_telegram_members_report
    res = send_telegram_members_report(
        target_name=req.app_name,
        search_date=req.search_date,
        reviews_data=req.reviews,
        service_type=req.service_type
    )
    return res

@app.post("/api/telegram/test")
async def api_test_telegram(req: TelegramTestRequest):
    res = test_telegram_connection(req.bot_token.strip(), req.chat_id.strip())
    return res

if __name__ == "__main__":
    print("=" * 60)
    print("   ARCEUS REVIEW FETCHER - AutoFetch System Started")
    print(f"   Dashboard: http://127.0.0.1:{PORT}")
    print("=" * 60)
    uvicorn.run(app, host=HOST, port=PORT, reload=False)

