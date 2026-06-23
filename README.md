# SAT Mistake Tracker

A local desktop helper for logging Digital-SAT mistakes. Paste or drop a
screenshot of a question you missed, let Gemini auto-classify it (topic,
subtopic, error type, root cause, fix strategy…), review, and save it to a
spreadsheet with the screenshot embedded. Optionally **sync live to a Google
Sheet** so a tutor/mentor can follow along and comment in real time.

> Runs entirely on your machine. Your API key and data never leave it, except
> the rows you choose to push to your own Google Sheet.

## Features

- Paste (`Cmd/Ctrl+V`), drag-and-drop, or grab-from-clipboard a screenshot.
- One-click **AI analysis** (Gemini) auto-fills the mistake fields; multiple
  API keys are tried in order (failover). AI is optional — manual logging works.
- Saves to `SAT_Performance_Tracker.xlsx` with the screenshot thumbnail + link.
- "Unsure how to solve" error type that disables the fields that don't apply.
- Optional **live Google Sheet sync** for mentor review.

## Requirements

- Python 3.10+
- macOS recommended (clipboard grab + Chrome app-mode launcher). It also runs
  on Windows/Linux via a normal browser tab; the "grab from clipboard" button
  is macOS-only.
- Google Chrome (optional, for the chromeless app window).

## Quick start

```bash
git clone <your-repo-url> sat-mistake-tracker
cd sat-mistake-tracker
cp .env.example .env          # then edit .env and add your Gemini key
./run.sh                      # creates the venv on first run, starts the app
```

Or manually:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py       # then open http://127.0.0.1:5001
```

Get a free Gemini key at <https://aistudio.google.com/apikey> (it starts with
`AIzaSy`). Paste it into `.env` as `GEMINI_API_KEY`, or via the in-app gear icon.

## Live sharing with a mentor (Google Sheet)

Each logged mistake is appended to a Google Sheet you control; your mentor opens
one link and watches it update live. Setup (~10 min, one time):

1. **Google Cloud:** create a project at <https://console.cloud.google.com>,
   then enable the **Google Sheets API** and **Google Drive API**.
2. **Service account:** IAM & Admin → Service Accounts → create one → add a
   **JSON key** → download it. Save it as `service_account.json` in this folder.
   (It's git-ignored — never commit it.)
3. **Create a Google Sheet.** Copy its ID from the URL
   (`/spreadsheets/d/<THIS_PART>/edit`).
4. **Share the Sheet** with:
   - the service-account email (found in the JSON, looks like
     `...@...iam.gserviceaccount.com`) → **Editor**
   - your mentor → **Viewer** or **Commenter**
5. *(Optional, for screenshots)* create a Drive folder, share it with the
   service account (**Editor**) and your mentor (**Viewer**), copy its folder ID.
6. Fill in `.env`:
   ```
   GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
   GSHEET_ID=<your sheet id>
   GSHEET_WORKSHEET=Mistakes
   GDRIVE_FOLDER_ID=<optional folder id>
   ```
7. Restart the app. From now on every saved mistake also lands in the shared
   Sheet. If Google is unreachable or unconfigured, local logging still works.

## Security

- **Never commit** `.env` or `service_account.json` — both are git-ignored.
- The service account only needs access to the one Sheet/folder you share with
  it (least privilege). Revoke by removing its share access.
- The app binds to `127.0.0.1` only; it is not exposed to your network.

## License

MIT — see [LICENSE](LICENSE).
