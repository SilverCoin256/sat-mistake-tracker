"""
Optional live sync to a shared Google Sheet (+ Drive for screenshots).

Design goals:
  * Zero impact when unconfigured — every function degrades gracefully so the
    local Excel logging always works even if Google is unreachable.
  * Service-account auth (no browser/OAuth flow, no token refresh to manage).
  * Scopes: spreadsheets + drive. Full drive (not drive.file) because the
    screenshots folder is shared to the service account by email from the
    user's own Drive, which drive.file's narrower visibility can't resolve
    as an upload parent.

Setup (see README "Live sharing"):
  1. Create a Google Cloud service account, enable Sheets API + Drive API,
     download its JSON key.
  2. Create a Google Sheet; share it with the service account email (Editor)
     and your mentor (Viewer/Commenter).
  3. (Optional) Create a Drive folder for screenshots; share it with the
     service account (Editor) and your mentor (Viewer). A second "Screenshots"
     tab is auto-created in the sheet with each mistake's screenshot embedded
     via =IMAGE(), alongside a lean subset of columns.
  4. Put the values in .env:
        GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
        GSHEET_ID=<spreadsheet id from its URL>
        GSHEET_WORKSHEET=Mistakes
        GDRIVE_FOLDER_ID=<optional folder id>
"""

import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    # Full Drive scope (not drive.file): the screenshots folder is shared to
    # the service account by email from the user's own Drive, not created or
    # picker-granted by this app, so drive.file's narrower visibility can't
    # see it as a valid upload parent.
    "https://www.googleapis.com/auth/drive",
]

# Order of columns written to the shared sheet.
HEADERS = [
    "Logged At", "Source / Site", "Section", "Correct Answer", "Your Answer",
    "Topic", "Subtopic", "Question Type", "Error Type", "Root Cause",
    "Fix Strategy", "Time Taken (Sec)", "Retest Status", "Notes", "Screenshot",
]

# Lean column set for the dedicated visual-review tab — just enough to
# identify the mistake next to its screenshot, not the full analysis.
SCREENSHOTS_TAB = "Screenshots"
SCREENSHOTS_HEADERS = ["Logged At", "Section", "Topic", "Correct", "Selected", "Screenshot"]


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


def _hex(h):
    h = h.lstrip("#")
    return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255, "blue": int(h[4:6], 16) / 255}


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
    """
    Upload a screenshot to Drive (link-viewable) and return both:
      - hyperlink: a =HYPERLINK(...) formula for the main sheet's Screenshot column
      - image_url: a direct-content thumbnail URL usable inside =IMAGE(...) for
        the dedicated Screenshots tab
    Returns {"hyperlink": "", "image_url": ""} when unconfigured or on failure —
    never raises (screenshot upload is always best-effort).
    """
    folder = os.getenv("GDRIVE_FOLDER_ID")
    if not folder or not screenshot_path or not os.path.exists(screenshot_path):
        return {"hyperlink": "", "image_url": ""}
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
    file_id = f.get("id", "")
    link = f.get("webViewLink", "")
    hyperlink = f'=HYPERLINK("{link}","View screenshot")' if link else ""
    # drive.google.com/thumbnail serves a direct image (not the Drive viewer
    # chrome), which is what Sheets' IMAGE() formula needs to render inline.
    image_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000" if file_id else ""
    return {"hyperlink": hyperlink, "image_url": image_url}


def _format_screenshots_tab(creds, spreadsheet_id, tab_id):
    """One-time visual formatting for a freshly-created Screenshots tab."""
    from googleapiclient.discovery import build
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    requests = [
        {"updateSheetProperties": {
            "properties": {"sheetId": tab_id, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount"}},
        {"repeatCell": {
            "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {
                "backgroundColor": _hex("1E3A5F"),
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "textFormat": {"foregroundColor": _hex("FFFFFF"), "bold": True, "fontSize": 10},
            }},
            "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)"}},
        {"updateDimensionProperties": {
            "range": {"sheetId": tab_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 34}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {
            "range": {"sheetId": tab_id, "dimension": "ROWS", "startIndex": 1, "endIndex": 500},
            "properties": {"pixelSize": 260}, "fields": "pixelSize"}},
    ]
    widths = [130, 100, 170, 70, 70, 440]  # Logged At, Section, Topic, Correct, Selected, Screenshot
    for i, w in enumerate(widths):
        requests.append({"updateDimensionProperties": {
            "range": {"sheetId": tab_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": w}, "fields": "pixelSize"}})
    svc.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()


def _open_screenshots_worksheet(creds):
    import gspread
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(os.getenv("GSHEET_ID"))
    try:
        ws = sh.worksheet(SCREENSHOTS_TAB)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=SCREENSHOTS_TAB, rows=500, cols=len(SCREENSHOTS_HEADERS))
        ws.update("A1", [SCREENSHOTS_HEADERS])
        _format_screenshots_tab(creds, os.getenv("GSHEET_ID"), ws.id)
    return ws


def _append_screenshot_row(creds, fields, image_url):
    """Best-effort append to the dedicated Screenshots tab. Never raises."""
    if not image_url:
        return
    from datetime import datetime
    ws = _open_screenshots_worksheet(creds)
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        fields.get("section", ""),
        fields.get("topic", ""),
        fields.get("correct_answer", ""),
        fields.get("your_answer", ""),
        f'=IMAGE("{image_url}")',
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


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
        image_url = ""
        try:
            upload = _upload_screenshot(creds, screenshot_path)
            screenshot_cell = upload["hyperlink"]
            image_url = upload["image_url"]
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
        try:
            _append_screenshot_row(creds, fields, image_url)
        except Exception:
            pass  # visual-review tab is a bonus, never block the main sync
        return {"ok": True, "url": f"https://docs.google.com/spreadsheets/d/{os.getenv('GSHEET_ID')}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
