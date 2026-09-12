"""
Zero-click ingestion: drop a screenshot (or PDF) into ~/Downloads/SAT Screenshots
and it is auto-analyzed, auto-saved to the local workbook, and auto-synced to
the shared Google Sheet — no browser, no review, no Save click.

Per-file logic:
  - Run the same circled-question detector the full-page/PDF upload flow
    uses. If it finds one or more circled numbers, save one row per circle
    (worksheet-page mode).
  - If it finds none, the file is treated as a single already-cropped
    mistake screenshot (the common case: a screenshot of just the one
    question that was missed) and run through the single-question
    extractor instead, saving exactly one row.
  - PDFs are rendered page-by-page (same resolution as the /analyze-pdf
    route) and each page goes through the same two-step logic above.

Processed files move to _processed/; files that fail (bad image, no API
key, etc.) move to _failed/ with a .error.txt sidecar — nothing is ever
silently dropped, but nothing ever blocks on a prompt either, since this
runs with no UI at all.

Run standalone:
    .venv/bin/python folder_watcher.py
Or install as a LaunchAgent (see install_watcher.sh) so it's always running.
"""
import os
import io
import time
import base64
import shutil
import traceback
from datetime import datetime

from PIL import Image as PILImage

from app import (
    gemini_keys, ensure_excel_exists,
    _detect_circled_questions, _analyze_single_question, save_mistake_row,
)

WATCH_DIR = os.path.expanduser("~/Downloads/SAT Screenshots")
PROCESSED_DIR = os.path.join(WATCH_DIR, "_processed")
FAILED_DIR = os.path.join(WATCH_DIR, "_failed")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
PDF_EXT = ".pdf"
POLL_SECONDS = 2
STABLE_CHECKS = 2  # consecutive size-unchanged polls before a file counts as fully written
TARGET_LONG_EDGE = 3000  # matches /analyze-pdf's resolution target


def _b64_of(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _row_from_circled(q, full_img):
    return {
        "source_site": "",
        "section": q.get("Section", ""),
        "correct_answer": q.get("Correct Answer", ""),
        "your_answer": q.get("Your Answer", ""),
        "topic": q.get("Topic", ""),
        "subtopic": q.get("Subtopic", ""),
        "question_type": q.get("Question Type", ""),
        "error_type": q.get("Error Type", ""),
        "root_cause": q.get("Root Cause", ""),
        "fix_strategy": q.get("Fix Strategy", ""),
        "time_taken": "",
        "retest_status": "Not Reviewed",
        "notes": q.get("Notes", ""),
        # A failed crop still deserves a saved row — attach the full page
        # rather than dropping the picture.
        "image": q.get("image") or _b64_of(full_img),
    }


def _row_from_single(analysis, full_img):
    return {
        "source_site": "",
        "section": analysis.get("Section", ""),
        "correct_answer": analysis.get("Correct Answer", ""),
        "your_answer": analysis.get("Your Answer", ""),
        "topic": analysis.get("Topic", ""),
        "subtopic": analysis.get("Subtopic", ""),
        "question_type": analysis.get("Question Type", ""),
        "error_type": analysis.get("Error Type", ""),
        "root_cause": analysis.get("Root Cause", ""),
        "fix_strategy": analysis.get("Fix Strategy", ""),
        "time_taken": "",
        "retest_status": "Not Reviewed",
        "notes": analysis.get("Notes", ""),
        "image": _b64_of(full_img),
    }


def process_page_image(full_img, keys, log):
    """One page/screenshot in. Saves 1+ rows. Returns (rows_saved, error)."""
    results, error = _detect_circled_questions(full_img, keys)
    if error:
        return 0, error

    if results:
        saved = 0
        for q in results:
            out, status = save_mistake_row(_row_from_circled(q, full_img))
            if out.get("success"):
                saved += 1
                log(f"saved row {out.get('row')} (Q{q.get('Question Number', '?')})")
            else:
                log(f"FAILED to save Q{q.get('Question Number', '?')}: {out.get('error')}")
        return saved, None

    # No circled numbers → this is a single already-cropped mistake screenshot.
    encoded = _b64_of(full_img).split(",", 1)[1]
    analysis, error, _key_used = _analyze_single_question(encoded, keys)
    if error:
        return 0, error

    out, status = save_mistake_row(_row_from_single(analysis, full_img))
    if out.get("success"):
        log(f"saved row {out.get('row')} (single question)")
        return 1, None
    return 0, out.get("error")


def process_file(path, log):
    ext = os.path.splitext(path)[1].lower()
    keys = gemini_keys()
    if not keys:
        return 0, "No Gemini API key configured — set it in the app's Settings panel first."

    if ext == PDF_EXT:
        import pymupdf
        with open(path, "rb") as f:
            doc = pymupdf.open(stream=f.read(), filetype="pdf")
        total_saved, errs = 0, []
        for i in range(doc.page_count):
            page = doc[i]
            zoom = TARGET_LONG_EDGE / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            page_img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
            n, err = process_page_image(page_img, keys, log)
            total_saved += n
            if err:
                errs.append(f"page {i + 1}: {err}")
        doc.close()
        return total_saved, ("; ".join(errs) if errs and total_saved == 0 else None)

    if ext in IMAGE_EXTS:
        img = PILImage.open(path).convert("RGB")
        return process_page_image(img, keys, log)

    return 0, f"Unsupported file type: {ext}"


def _is_stable(path):
    """True once the file's size hasn't changed across STABLE_CHECKS polls —
    guards against reading a screenshot mid-write (Finder paste/drag isn't
    always one atomic write)."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return False
    for _ in range(STABLE_CHECKS):
        time.sleep(0.4)
        try:
            new_size = os.path.getsize(path)
        except OSError:
            return False
        if new_size != size:
            return False
        size = new_size
    return True


def main():
    ensure_excel_exists()
    for d in (WATCH_DIR, PROCESSED_DIR, FAILED_DIR):
        os.makedirs(d, exist_ok=True)

    print(f"[watcher] watching: {WATCH_DIR}")
    print("[watcher] drop a screenshot or PDF in — it saves itself, no review needed.")
    # Anything already sitting there at startup is presumed already handled
    # (or intentionally left) — only react to files that show up from here on.
    seen = set(os.listdir(WATCH_DIR))

    while True:
        try:
            names = [n for n in os.listdir(WATCH_DIR)
                     if not n.startswith(".") and n not in ("_processed", "_failed")]
        except FileNotFoundError:
            os.makedirs(WATCH_DIR, exist_ok=True)
            time.sleep(POLL_SECONDS)
            continue

        for name in names:
            if name in seen:
                continue
            path = os.path.join(WATCH_DIR, name)
            if not os.path.isfile(path):
                continue
            if os.path.splitext(name)[1].lower() not in (IMAGE_EXTS | {PDF_EXT}):
                seen.add(name)
                continue
            if not _is_stable(path):
                continue  # still being written — check again next poll, don't mark seen

            seen.add(name)
            ts = datetime.now().strftime("%H:%M:%S")

            def log(msg, _ts=ts, _name=name):
                print(f"[{_ts}] {_name}: {msg}")

            log("processing...")
            try:
                n, err = process_file(path, log)
            except Exception as e:
                n, err = 0, f"{e}\n{traceback.format_exc()}"

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if n > 0:
                shutil.move(path, os.path.join(PROCESSED_DIR, f"{stamp}_{name}"))
                log(f"done — {n} row(s) added.")
                if err:
                    log(f"(partial failure on remaining content) {err}")
            else:
                dest = os.path.join(FAILED_DIR, f"{stamp}_{name}")
                shutil.move(path, dest)
                with open(dest + ".error.txt", "w") as f:
                    f.write(err or "unknown error")
                log(f"FAILED — moved to _failed/. {err}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
