# 🌟 ARCEUS REVIEW FETCHER — AutoFetch System

High-performance Auto-Fetch and Review Verification System designed specifically for **App Reviews** (Google Play Store) and **Map Reviews** (Google Maps) with smart comment matching, live units counting, and invoice export.

---

## 🚀 Quick Start (1-Click Run)

Just double-click **`run.bat`** on your desktop, or run in terminal:
```bash
python main.py
```
Then open your browser at: **`http://127.0.0.1:5000`**

---

## 🧪 How to Test (Examples You Can Give)

### Example 1: 📱 App Review Test (Play Store)
1. Select **📱 App Review** tab.
2. **Target Package ID**: Enter any app package ID or URL, for example:
   - `com.whatsapp`
   - `com.dream11.android`
   - `com.fibe.app`
3. **Target Date**: Select today's date (or any recent date).
4. **Star Rating**: Choose `5 Stars` (or `All Stars`).
5. **Search Comments / Keywords / Symbols**:
   - Paste words like:
     ```
     smooth
     payment
     fast
     good
     ..
     !
     ```
6. Click **⚡ Fetch Reviews Now**.
7. The system scans the live reviews from Google Play, highlights matched keywords, counts your **Live Units**, and lets you download CSV with 1 click!

### Example 2: 🔄 Background Auto-Fetch Test
1. Set **Auto-Fetch Interval** (e.g. `Every 5 mins` or `Every 2 mins`).
2. Click **🔄 Start Auto-Fetch**.
3. The system will automatically poll Google Play in the background, update your live counts, and send alerts whenever new reviews go live matching your comments.

### Example 4: 📅 8-Day Retention Auto-Checker (Telegram Bot)
1. Select the **📅 8-Day Auto-TG** tab on the top left.
2. **Campaign App Package ID**: Enter the app package given on Day 1 (e.g. `com.whatsapp` or your campaign app).
3. **List Date (Day 1)**: Today's date (or the date the campaign was assigned).
4. **Search Comments / Keywords / Symbols**: Paste comments, keywords, or trailing symbols (e.g. `fast`, `..`, `!`).
5. **Member Roster (Optional)**: Paste your team members' names.
6. Click **📅 Save & Schedule 8-Day Task**:
   - The task is registered in the database with a live countdown (e.g., *7 days remaining*).
   - On the **8th day**, the background system **automatically wakes up**, scans Google Play Store, counts all live units, generates a formatted summary report, and **sends the report + CSV file directly to your Telegram Bot**!
   - You can also click **⚡ Check & Send TG** anytime in the table to test or force-send the report immediately!

---

## ⚙️ Setting Up Your Telegram Bot

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` to create your bot and copy the **Bot Token** (e.g., `123456:ABC-DEF...`).
3. Start a chat with your new bot (send `/start`), or add it to your Telegram review group.
4. Get your **Chat ID** (via `@userinfobot` or group ID like `-100...`).
5. On the dashboard, click **⚙️ Settings**, paste your **Bot Token** and **Chat ID**, and click **🔔 Send Test Telegram Message** to verify!

## 📁 Project Architecture

- `main.py` — FastAPI web server & REST endpoints.
- `fetcher_app.py` — High-speed Google Play Store review engine.
- `fetcher_map.py` — Google Maps place resolver & review engine.
- `matcher.py` — Smart comment, symbol (`.`, `..`, `!`), and member matcher.
- `scheduler.py` — Background APScheduler automated periodic monitoring.
- `database.py` — SQLite database (`arceus_reviews.db`) saving all matched live units.
- `integrations.py` — Google Sheet Webhook sync, Telegram Bot alerts, CSV export.
- `templates/` & `static/` — Modern Arceus dark/gold dashboard UI.
- `run.bat` — 1-click Windows launcher.

