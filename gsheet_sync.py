"""
Optional live sync to a shared Google Sheet (+ Drive for screenshots).

Design goals:
  * Zero impact when unconfigured — every function degrades gracefully so the
    local Excel logging always works even if Google is unreachable.
  * Service-account auth (no browser/OAuth flow, no token refresh to manage).
  * Least privilege: spreadsheets + drive.file (only files this app creates).

Setup (see README "Live sharing"):
  1. Create a Google Cloud service account, enable Sheets API + Drive API,
     download its JSON key.
  2. Create a Google Sheet; share it with the service account email (Editor)
     and your mentor (Viewer/Commenter).
  3. (Optional) Create a Drive folder for screenshots; share it with the
     service account (Editor) and your mentor (Viewer).
  4. Put the values in .env:
        GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
        GSHEET_ID=<spreadsheet id from its URL>
        GSHEET_WORKSHEET=Mistakes
        GDRIVE_FOLDER_ID=<optional folder id>
"""

import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Order of columns written to the shared sheet.
HEADERS = [
    "Logged At", "Source / Site", "Section", "Correct Answer", "Your Answer",
    "Topic", "Subtopic", "Question Type", "Error Type", "Root Cause",
    "Fix Strategy", "Time Taken (Sec)", "Retest Status", "Notes", "Screenshot",
]


def _sa_path():
    return os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")


def is_enabled():
    """True only when a service-account key file and a target sheet are set."""
    return bool(os.getenv("GSHEET_ID")) and os.path.exists(_sa_path())


def status():
    """Lightweight status for the UI / health checks (no network call)."""
    return {
        "configured": is_enabled(),
        "has_credentials": os.path.exists(_sa_path()),
        "has_sheet_id": bool(os.getenv("GSHEET_ID")),
        "drive_uploads": bool(os.getenv("GDRIVE_FOLDER_ID")),
    }


def _credentials():
    # Imported lazily so the app runs even if Google libs aren't installed.
    from google.oauth2.service_account import Credentials
    return Credentials.from_service_account_file(_sa_path(), scopes=SCOPES)


def _open_worksheet(creds):
    import gspread
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(os.getenv("GSHEET_ID"))
    name = os.getenv("GSHEET_WORKSHEET", "Mistakes")
    try:
        ws = sh.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=1000, cols=len(HEADERS))
    # Ensure a header row exists exactly once.
    if not ws.acell("A1").value:
        ws.update("A1", [HEADERS])
    return ws


def _upload_screenshot(creds, screenshot_path):
    """Upload a screenshot to Drive (link-viewable) and return a HYPERLINK formula."""
    folder = os.getenv("GDRIVE_FOLDER_ID")
    if not folder or not screenshot_path or not os.path.exists(screenshot_path):
        return ""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    meta = {"name": os.path.basename(screenshot_path), "parents": [folder]}
    media = MediaFileUpload(screenshot_path, mimetype="image/png")
    f = drive.files().create(body=meta, media_body=media,
                             fields="id, webViewLink").execute()
    # Anyone with the link can view (mentor needs no extra grant).
    drive.permissions().create(fileId=f["id"],
                               body={"role": "reader", "type": "anyone"}).execute()
    link = f.get("webViewLink", "")
    return f'=HYPERLINK("{link}","View screenshot")' if link else ""


def append_row(fields, screenshot_path=None):
    """
    Append one mistake to the shared sheet. Returns {ok, url?, error?}.
    Never raises — callers can ignore failures and keep local logging intact.
    """
    if not is_enabled():
        return {"ok": False, "skipped": True, "error": "Google sync not configured"}
    try:
        from datetime import datetime
        creds = _credentials()
        ws = _open_worksheet(creds)
        screenshot_cell = ""
        try:
            screenshot_cell = _upload_screenshot(creds, screenshot_path)
        except Exception as e:  # screenshot upload is non-fatal
            screenshot_cell = f"(screenshot upload failed: {e})"
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            fields.get("source_site", ""), fields.get("section", ""),
            fields.get("correct_answer", ""), fields.get("your_answer", ""),
            fields.get("topic", ""), fields.get("subtopic", ""),
            fields.get("question_type", ""), fields.get("error_type", ""),
            fields.get("root_cause", ""), fields.get("fix_strategy", ""),
            fields.get("time_taken", ""), fields.get("retest_status", ""),
            fields.get("notes", ""), screenshot_cell,
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return {"ok": True, "url": f"https://docs.google.com/spreadsheets/d/{os.getenv('GSHEET_ID')}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
