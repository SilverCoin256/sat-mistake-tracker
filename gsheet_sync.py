"""
Optional live sync to a shared Google Sheet (+ Cloud Storage for screenshots).

Design goals:
  * Zero impact when unconfigured — every function degrades gracefully so the
    local Excel logging always works even if Google is unreachable.
  * Service-account auth (no browser/OAuth flow, no token refresh to manage).
  * Scopes: spreadsheets + Cloud Storage read/write.

Screenshots use GCS, not Drive: a bare service account cannot upload to
Drive on a personal (non-Workspace) account — Google blocks it with
"Service Accounts do not have storage quota", even when the target folder
is explicitly shared to the SA by a human owner (confirmed empirically,
contradicts the commonly-cited "share a folder" workaround, which appears
to only apply to Workspace/Shared-Drive setups). GCS has no such
restriction — objects are billed to the GCP project, not a personal quota.
Bucket objects are public-read (unlisted URL, same exposure level as a
Drive "anyone with the link" share) so Sheets' IMAGE() formula and the
mentor can both load them with no extra auth.

Setup (see README "Live sharing"):
  1. Create a Google Cloud service account, enable Sheets API + Cloud
     Storage API, download its JSON key. Ensure the project has Cloud
     Billing enabled (required by GCS, even on free-tier usage).
  2. Create a Google Sheet; share it with the service account email (Editor)
     and your mentor (Viewer/Commenter).
  3. (Optional) Create a GCS bucket, grant the service account
     roles/storage.objectAdmin on it, and grant allUsers
     roles/storage.objectViewer for public read. A second "Screenshots" tab
     is auto-created in the sheet with each mistake's screenshot embedded
     via =IMAGE(), alongside a lean subset of columns.
  4. Put the values in .env:
        GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
        GSHEET_ID=<spreadsheet id from its URL>
        GSHEET_WORKSHEET=Mistakes
        GCS_BUCKET=<optional bucket name>
"""

import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/devstorage.read_write",
]

# Order of columns written to the shared sheet.
HEADERS = [
    "Logged At", "Source / Site", "Section", "Correct Answer", "Your Answer",
    "Topic", "Subtopic", "Question Type", "Error Type", "Root Cause",
    "Fix Strategy", "Time Taken (Sec)", "Retest Status", "Notes", "Screenshot",
]

# Column set for the dedicated visual-review tab — the fields that matter
# when reviewing a mistake next to its screenshot (full analysis stays in
# the main Mistakes tab).
SCREENSHOTS_TAB = "Screenshots"
SCREENSHOTS_HEADERS = [
    "Logged At", "Source", "Section", "Topic", "Subtopic",
    "Correct", "Selected", "Error Type", "Fix Strategy", "Screenshot",
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
        "screenshot_uploads": bool(os.getenv("GCS_BUCKET")),
    }


def _hex(h):
    h = h.lstrip("#")
    return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255, "blue": int(h[4:6], 16) / 255}


def _cell(value):
    """
    Neutralize spreadsheet formula injection. Rows are appended with
    USER_ENTERED (needed so our own =HYPERLINK/=IMAGE cells work), which
    means user-supplied text beginning with "=" or "+" would otherwise be
    executed as a live formula. Prefixing an apostrophe forces plain text;
    Sheets hides the apostrophe when displaying.
    """
    s = "" if value is None else str(value)
    return "'" + s if s.startswith(("=", "+")) else s


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
    Upload a screenshot to the GCS bucket (public-read) and return both:
      - hyperlink: a =HYPERLINK(...) formula for the main sheet's Screenshot column
      - image_url: a direct public URL usable inside =IMAGE(...) for the
        dedicated Screenshots tab
    Returns {"hyperlink": "", "image_url": ""} when unconfigured or on failure —
    never raises (screenshot upload is always best-effort).
    """
    bucket = os.getenv("GCS_BUCKET")
    if not bucket or not screenshot_path or not os.path.exists(screenshot_path):
        return {"hyperlink": "", "image_url": ""}
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    storage = build("storage", "v1", credentials=creds, cache_discovery=False)
    object_name = f"screenshots/{os.path.basename(screenshot_path)}"
    media = MediaFileUpload(screenshot_path, mimetype="image/png")
    storage.objects().insert(bucket=bucket, name=object_name, media_body=media,
                             fields="name").execute()
    # Bucket-level allUsers:objectViewer IAM binding (set up once, outside the
    # app) already makes every object public — no per-object ACL call needed.
    url = f"https://storage.googleapis.com/{bucket}/{object_name}"
    return {"hyperlink": f'=HYPERLINK("{url}","View screenshot")', "image_url": url}


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
    # Logged At, Source, Section, Topic, Subtopic, Correct, Selected,
    # Error Type, Fix Strategy, Screenshot
    widths = [130, 175, 100, 150, 175, 68, 68, 185, 195, 440]
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
        _cell(fields.get("source_site", "")),
        _cell(fields.get("section", "")),
        _cell(fields.get("topic", "")),
        _cell(fields.get("subtopic", "")),
        _cell(fields.get("correct_answer", "")),
        _cell(fields.get("your_answer", "")),
        _cell(fields.get("error_type", "")),
        _cell(fields.get("fix_strategy", "")),
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
            _cell(fields.get("source_site", "")), _cell(fields.get("section", "")),
            _cell(fields.get("correct_answer", "")), _cell(fields.get("your_answer", "")),
            _cell(fields.get("topic", "")), _cell(fields.get("subtopic", "")),
            _cell(fields.get("question_type", "")), _cell(fields.get("error_type", "")),
            _cell(fields.get("root_cause", "")), _cell(fields.get("fix_strategy", "")),
            fields.get("time_taken", ""), _cell(fields.get("retest_status", "")),
            _cell(fields.get("notes", "")), screenshot_cell,
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        try:
            _append_screenshot_row(creds, fields, image_url)
        except Exception:
            pass  # visual-review tab is a bonus, never block the main sync
        return {"ok": True, "url": f"https://docs.google.com/spreadsheets/d/{os.getenv('GSHEET_ID')}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
