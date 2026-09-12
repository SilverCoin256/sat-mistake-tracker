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

# Column set for the dedicated visual-review tab. Screenshot leads (it's the
# point of this tab); "Image Link" is the RAW URL as plain text, not a
# =HYPERLINK() formula. Two things were verified empirically, not assumed:
# (1) copying an =IMAGE() cell puts only HTML/formula text on the clipboard
#     (Cmd+C then `osascript -e 'clipboard info'` showed no image type at
#     all) — there's no way to paste a real picture out of one.
# (2) =HYPERLINK() cells are NOT a reliable fix for that: Sheets' click-to-
#     navigate affordance for a hyperlink cell (chip-on-hover, click again
#     to open) turned out to be inconsistent — repeated real attempts
#     (plain click, re-click, Cmd+click, hover) failed to open the link.
# A plain-text cell has none of that ambiguity: select it, Cmd+C copies the
# literal URL text (guaranteed — it's not a formula or rendered object),
# paste into a new tab's address bar, and that page is a real <img> where
# right-click → Copy Image puts actual pixels on the clipboard. One extra
# manual step (paste into the address bar) traded for zero flakiness.
SCREENSHOTS_TAB = "Screenshots"
SCREENSHOTS_HEADERS = [
    "Screenshot", "Image Link (copy, paste in new tab)", "Logged At", "Source",
    "Section", "Topic", "Subtopic", "Correct", "Selected", "Error Type", "Fix Strategy",
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
    """One-time visual formatting for a freshly-created Screenshots tab.
    Screenshot is the dominant column (big, first, centered) since it's the
    entire point of this tab; everything else is compact reference data."""
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
        {"repeatCell": {
            "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"backgroundColor": _hex("0B5FA5"), "textFormat": {"fontSize": 12, "bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"updateDimensionProperties": {
            "range": {"sheetId": tab_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 40}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {
            "range": {"sheetId": tab_id, "dimension": "ROWS", "startIndex": 1, "endIndex": 500},
            "properties": {"pixelSize": 420}, "fields": "pixelSize"}},
        {"repeatCell": {
            "range": {"sheetId": tab_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}},
            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"}},
        {"repeatCell": {
            "range": {"sheetId": tab_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {"userEnteredFormat": {
                "horizontalAlignment": "LEFT", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP",
                "textFormat": {"foregroundColor": _hex("444444"), "fontSize": 8}}},
            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,wrapStrategy,textFormat)"}},
        {"repeatCell": {
            "range": {"sheetId": tab_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": 11},
            "cell": {"userEnteredFormat": {"verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP", "textFormat": {"fontSize": 10}}},
            "fields": "userEnteredFormat(verticalAlignment,wrapStrategy,textFormat)"}},
    ]
    # Screenshot, Image Link, Logged At, Source, Section, Topic, Subtopic,
    # Correct, Selected, Error Type, Fix Strategy
    widths = [620, 160, 125, 165, 95, 145, 170, 65, 65, 180, 190]
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
    target_row = len(ws.get_all_values()) + 1
    row = [
        f'=IMAGE("{image_url}")',
        "",  # link column filled separately below, as RAW so it stays plain text
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        _cell(fields.get("source_site", "")),
        _cell(fields.get("section", "")),
        _cell(fields.get("topic", "")),
        _cell(fields.get("subtopic", "")),
        _cell(fields.get("correct_answer", "")),
        _cell(fields.get("your_answer", "")),
        _cell(fields.get("error_type", "")),
        _cell(fields.get("fix_strategy", "")),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
    # USER_ENTERED (needed above so =IMAGE renders) auto-linkifies a bare URL
    # into a clickable rich-text hyperlink — the exact fragility this design
    # avoids. RAW mode on just this cell keeps it inert, selectable text.
    ws.update(f"B{target_row}", [[image_url]], value_input_option="RAW")


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
