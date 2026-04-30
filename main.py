from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import csv
import os
import json
import re
import urllib.request
from datetime import datetime

app = FastAPI(title="VAPI BFSI Backend")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
CSV_FILE = "data/calls_data.csv"
DEBUG_LOG = "data/debug_log.json"
RECORDINGS_DIR = "data/recordings"
CSV_HEADERS = [
    "Timestamp",
    "Call ID",
    "Customer Name",
    "Interested",
    "Has Gold",
    "Loan Amount",
    "Employment",
    "Duration",
    "Status",
    "Qualification Status",
    "Recording URL",
    "Stereo Recording URL",
    "Recording File",
    "Stereo Recording File",
    "Transcript",
]


def to_bool_for_migration(value):
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def ensure_csv_schema():
    """
    Ensure CSV always uses the current header format.
    If an old schema is found, migrate rows and create backup.
    """
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        return

    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        first_row = next(reader, [])

    if first_row == CSV_HEADERS:
        return

    backup_file = CSV_FILE.replace(".csv", "_backup.csv")

    try:
        # Read old file first (works even if another app has a soft lock)
        with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            _ = next(reader, None)  # old header
            old_rows = list(reader)

        migrated_rows = []
        for row in old_rows:
            if not row:
                continue

            if len(row) >= 15:
                migrated_rows.append(row[:15])
                continue

            # Old format with Phone Number column (9 columns)
            if len(row) == 9:
                timestamp, call_id, _phone, customer_name, interested, has_gold, loan_amt, employment, transcript = row
            # Older format without Phone Number (8 columns)
            elif len(row) == 8:
                timestamp, call_id, customer_name, interested, has_gold, loan_amt, employment, transcript = row
            else:
                continue

            interested_bool = to_bool_for_migration(interested)
            has_gold_bool = to_bool_for_migration(has_gold)
            qualification = "Qualified" if (interested_bool and has_gold_bool) else ("Not Interested" if not interested_bool else "Disqualified")

            migrated_rows.append([
                timestamp,
                call_id,
                customer_name or "Unknown",
                interested_bool,
                has_gold_bool,
                loan_amt or 0,
                employment or "Unknown",
                0,
                "Completed",
                qualification,
                "",
                "",
                "",
                "",
                transcript or "",
            ])

        # Write migration to temp file first
        temp_file = CSV_FILE.replace(".csv", "_migrated_tmp.csv")
        with open(temp_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            writer.writerows(migrated_rows)

        # Backup copy (best effort; may fail if file locked)
        try:
            with open(backup_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(first_row)
                writer.writerows(old_rows)
            print(f"📦 Old CSV backup saved at: {backup_file}")
        except Exception as backup_err:
            print(f"⚠️ Could not write backup file: {backup_err}")

        # Replace original (if locked, keep running and ask user to close file once)
        try:
            os.replace(temp_file, CSV_FILE)
            print("✅ CSV schema migrated to latest format.")
        except PermissionError:
            print("⚠️ CSV is currently in use. Close CSV/Excel/Streamlit view once and restart backend to complete migration.")
            # Do not crash startup; keep old file for now.
            if os.path.exists(temp_file):
                os.remove(temp_file)
    except Exception as migration_err:
        print(f"⚠️ CSV migration skipped: {migration_err}")


@app.on_event("startup")
async def startup_event():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    ensure_csv_schema()


def download_recording(url, call_id, suffix):
    if not url:
        return ""

    try:
        filename = f"{call_id}_{suffix}.wav"
        local_path = os.path.join(RECORDINGS_DIR, filename)
        urllib.request.urlretrieve(url, local_path)
        return local_path
    except Exception as e:
        print(f"⚠️ Recording download failed ({suffix}): {e}")
        return ""

@app.get("/")
def read_root():
    return {"message": "VAPI Backend is running successfully!"}


def extract_structured_outputs(message):
    """
    Extract structured outputs safely from VAPI message.
    Handles multiple possible locations.
    """
    extracted = {}

    # 🔥 Primary location (correct one)
    artifact = message.get("artifact", {})
    raw = artifact.get("structuredOutputs", {})

    for uid, obj in raw.items():
        name = obj.get("name")
        result = obj.get("result")
        if name:
            extracted[name] = result

    # 🔥 Backup (if VAPI changes format)
    if not extracted:
        analysis = message.get("analysis", {})
        extracted = analysis.get("structuredData", {})

    return extracted


def extract_transcript(message):
    """
    Safely extract transcript
    """
    transcript = message.get("transcript")

    # fallback if transcript missing
    if not transcript:
        transcript = json.dumps(message.get("artifact", {}).get("messages", []))

    return transcript


def normalize_name(value):
    if value is None:
        return "Unknown"
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "unknown", "na", "n/a"}:
        return "Unknown"
    return text.title()


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {
        "true", "yes", "y", "interested", "ok", "sure", "haan", "ha", "maybe", "callback"
    }


def normalize_loan_amount(value):
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return 0.0

    text = str(value).strip().lower().replace(",", "")
    if not text:
        return 0.0

    number_match = re.search(r"\d+(\.\d+)?", text)
    if not number_match:
        return 0.0

    amount = float(number_match.group())
    if "lakh" in text or "lac" in text:
        amount *= 100000
    elif "thousand" in text or "k" in text:
        amount *= 1000

    return float(amount)


def derive_qualification(is_interested, has_gold):
    if not is_interested:
        return "Not Interested"
    if is_interested and has_gold:
        return "Qualified"
    return "Disqualified"


@app.post("/webhook")
async def vapi_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"message": "Invalid JSON"})

    # Save debug log
    with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(payload, indent=2, default=str) + "\n---END---\n")

    message = payload.get("message", {})
    msg_type = message.get("type", "")

    print(f"\n📨 Webhook received! Type: {msg_type}")

    # ✅ IMPORTANT FIX: handle both event types
    if msg_type not in ["end-of-call-report", "call.ended"]:
        print("⏭️ Not final event, skipping...")
        return {"status": "ignored"}

    print("✅ Processing final call...")

    try:
        # Call info
        call = message.get("call", {})
        call_id = call.get("id", "Unknown")

        # Extract transcript
        transcript = extract_transcript(message)
        recording_url = message.get("recordingUrl", "")
        stereo_recording_url = message.get("stereoRecordingUrl", "")
        recording_file = download_recording(recording_url, call_id, "mono")
        stereo_recording_file = download_recording(stereo_recording_url, call_id, "stereo")

        # Extract structured data
        structured_data = extract_structured_outputs(message)

        print(f"📊 Structured Data: {json.dumps(structured_data, indent=2)}")

        # Fields
        cust_name = normalize_name(structured_data.get("customer_name", "Unknown"))
        interested = normalize_bool(structured_data.get("is_interested", False))
        has_gold = normalize_bool(structured_data.get("has_physical_gold", False))
        loan_amt = normalize_loan_amount(structured_data.get("loan_amount", 0))
        employment = str(structured_data.get("employment_type", "Unknown")).strip() or "Unknown"
        qualification_status = derive_qualification(interested, has_gold)

        duration = (
            call.get("duration") or
            call.get("durationSeconds") or
            message.get("duration") or
            0
        )
        status = message.get("endedReason") or call.get("status") or "Completed"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save CSV
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, call_id, cust_name,
                interested, has_gold, loan_amt, employment,
                duration, status, qualification_status,
                recording_url, stereo_recording_url,
                recording_file, stereo_recording_file,
                transcript
            ])

        print("\n" + "=" * 50)
        print(f"✅ Call Stored Successfully!")
        print(f"🆔 Call ID: {call_id}")
        print(f"👤 Name: {cust_name}")
        print(f"💰 Loan: {loan_amt}")
        print(f"📈 Interested: {interested}")
        print(f"🏅 Has Gold: {has_gold}")
        print("💾 Saved to CSV")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"❌ ERROR processing webhook: {str(e)}")

    return {"status": "success"}