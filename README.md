# SAT Mistake Tracker

Log missed Digital SAT questions in a local Excel workbook. Paste a screenshot, fill in the mistake fields or let Gemini suggest them, then review the entry before saving. Google Sheets sync is optional.

## Where the data goes

Manual logging saves the entry and screenshot locally. AI analysis sends the screenshot to Gemini using a configured API key. Google Sheets sync sends the logged fields to the configured sheet. When you also configure a Cloud Storage bucket for screenshots, the app uploads screenshots to that bucket. The setup below makes those images accessible to anyone with their URLs.

## Features

- Paste (`Cmd/Ctrl+V`), drag-and-drop, or grab-from-clipboard a screenshot.
- Optional Gemini analysis suggests values for the mistake fields. If a configured API key fails, the app tries the next one.
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
   then enable the **Google Sheets API** and **Cloud Storage API**. Cloud
   Storage requires Cloud Billing to be enabled on the project (free-tier
   usage for this is effectively free, but a payment method must be on file).
2. **Service account:** IAM & Admin → Service Accounts → create one → add a
   **JSON key** → download it. Save it as `service_account.json` in this folder.
   (It's git-ignored — never commit it.)
3. **Create a Google Sheet.** Copy its ID from the URL
   (`/spreadsheets/d/<THIS_PART>/edit`).
4. **Share the Sheet** with:
   - the service-account email (found in the JSON, looks like
     `...@...iam.gserviceaccount.com`) → **Editor**
   - your mentor → **Viewer** or **Commenter**
5. *(Optional, for screenshots)* create a Cloud Storage bucket, then grant it:
   - the service-account email → **Storage Object Admin** (bucket-level IAM)
   - `allUsers` → **Storage Object Viewer** (bucket-level IAM; makes uploaded
     screenshots reachable by an unlisted URL — same exposure as a Drive
     "anyone with the link" share)

   Note: a bare service account **cannot** upload to Google Drive on a
   personal (non-Workspace) account — Google blocks it with "Service
   Accounts do not have storage quota", even if the folder is shared to it
   by a human owner. Cloud Storage is the working alternative.
6. Fill in `.env`:
   ```
   GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
   GSHEET_ID=<your sheet id>
   GSHEET_WORKSHEET=Mistakes
   GCS_BUCKET=<optional bucket name>
   ```
7. Restart the app. From now on every saved mistake also lands in the shared
   Sheet. If you set up the bucket in step 5, the **Screenshots** tab embeds
   uploaded images with `=IMAGE()`. Local logging works independently of Google Sheets.

## Security

- **Never commit** `.env` or `service_account.json` — both are git-ignored.
- The service account only needs access to the one Sheet/folder you share with
  it (least privilege). Revoke by removing its share access.
- The app binds to `127.0.0.1` only; it is not exposed to your network.

## License

MIT — see [LICENSE](LICENSE).
