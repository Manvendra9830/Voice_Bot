# BFSI Voice AI - Gold Loan Lead Qualification

Production-style, locally runnable outbound voice agent for BFSI lead qualification (Gold Loan).

This project is intentionally lightweight (FastAPI + CSV + Streamlit), but covers complete demo flow:
mobile/web call -> Vapi assistant -> webhook -> extraction + normalization -> CSV -> dashboard analytics.

## 1) Project Goal

Build and demonstrate a voice agent that:
- checks interest in Gold Loan
- qualifies lead (gold availability, loan amount, employment)
- follows BFSI-safe compliance behavior
- stores structured outputs + transcript + recording references
- exposes simple analytics and transcript/replay view for stakeholders

## 2) Tech Stack

- `Vapi` - call orchestration and assistant runtime
- `Gemini 2.0 Flash` - conversation model (configured in Vapi)
- `OpenAI TTS / selected cloned voice` - voice synthesis (configured in Vapi)
- `Deepgram` - transcription (configured in Vapi)
- `FastAPI` - webhook backend (`main.py`)
- `ngrok` - public tunnel to local webhook
- `CSV` - lightweight storage (`data/calls_data.csv`)
- `Streamlit + Pandas` - dashboard and basic analytics

## 3) Folder and File Roles

- `main.py`  
  Webhook entrypoint. Handles final call events, normalizes fields, computes qualification status, stores CSV rows, and downloads recording files when available.

- `assistant_config.py`  
  Version-controlled prompt and structured extraction schema reference.

- `dashboard.py`  
  Streamlit app with filters, metrics, charts, transcript viewer, and audio playback from local files/URLs.

- `intent_mapping.json`  
  Intent taxonomy, slot definitions, sample utterances, required/optional slot metadata.

- `test_cases.json`  
  Structured list of test scenarios.

- `test_harness.py`  
  Lightweight automated validation against normalization logic.

- `demo_call_scripts.md`  
  Scripted flows for success, failure, and compliance demos.

- `requirements.txt`  
  Python package dependencies.

- `data/calls_data.csv`  
  Runtime lead storage (generated locally; ignored in git).

- `data/calls_data.sample.csv`  
  Header-only sample schema for repository/reference.

- `.gitignore`  
  Excludes generated logs, recordings, CSV runtime data, cache, and secrets from GitHub.

## 4) Data Schema (CSV)

`calls_data.csv` columns:

1. `Timestamp`  
2. `Call ID`  
3. `Customer Name`  
4. `Interested`  
5. `Has Gold`  
6. `Loan Amount`  
7. `Employment`  
8. `Duration`  
9. `Status`  
10. `Qualification Status`  
11. `Recording URL`  
12. `Stereo Recording URL`  
13. `Recording File`  
14. `Stereo Recording File`  
15. `Transcript`

## 5) End-to-End Data Flow

1. Outbound call is triggered from Vapi (web call or phone call via Twilio-linked number).
2. Assistant runs configured script and extracts structured outputs.
3. Vapi sends server events to `/webhook`.
4. Backend ignores non-final events and processes `end-of-call-report` / `call.ended`.
5. Backend:
   - extracts structured data
   - normalizes name/boolean/loan amount
   - derives qualification status
   - stores transcript + recording URLs
   - attempts local recording download
6. Row is appended to `data/calls_data.csv`.
7. Dashboard reads CSV and presents filters, metrics, charts, transcripts, and audio playback.

## 6) Architecture (Logical)

- **Channel Layer**: Vapi call channel (web/mobile)
- **AI Layer**: Vapi assistant model + voice + transcriber
- **Integration Layer**: FastAPI webhook (`/webhook`)
- **Storage Layer**: CSV + local recording files
- **Presentation Layer**: Streamlit dashboard

## 7) Full Setup and Runbook (Command by Command)

Run from project folder:

```powershell
cd C:\Users\Manvendra Singh\Desktop\Assessment\vapi_backend
```

### A) Environment setup

```powershell
conda activate vapi_env
pip install -r requirements.txt
```

### B) Start backend (Terminal 1)

```powershell
conda activate vapi_env
cd C:\Users\Manvendra Singh\Desktop\Assessment\vapi_backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### C) Start ngrok tunnel (Terminal 2)

```powershell
ngrok http 8000
```

Use forwarding URL in Vapi server config:

`https://<ngrok-id>.ngrok-free.app/webhook`

### D) Start dashboard (Terminal 3)

```powershell
conda activate vapi_env
cd C:\Users\Manvendra Singh\Desktop\Assessment\vapi_backend
streamlit run dashboard.py
```

### E) Trigger outbound call via API (optional mobile test)

```powershell
$headers = @{
  Authorization = "Bearer <VAPI_API_KEY>"
  "Content-Type" = "application/json"
}

$body = @{
  assistantId = "<ASSISTANT_ID>"
  phoneNumberId = "<PHONE_NUMBER_ID>"
  customer = @{
    number = "+91XXXXXXXXXX"
  }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/call" -Headers $headers -Body $body
```

### F) Run local test harness

```powershell
python test_harness.py
```

## 8) Dashboard Capabilities

- Filters: date range, interest, minimum amount, qualification, compliance keyword match
- Metrics: total calls, interested leads, success rate, average loan amount, compliance hits
- Charts: interest split, loan trend, qualification breakdown
- Transcript explorer by Call ID
- Recording links + local audio playback when files are available

## 9) Compliance Behavior Implemented

- No OTP/PIN/CVV/full Aadhaar/full PAN collection in flow
- Safety warning response when user shares sensitive information
- No guaranteed approval claim
- Structured lead extraction without exposing secret credentials in code

## 10) Test and Demo Guidance

Recommended demo calls:
- Success path: interested + has gold + next step accepted
- Failure path: not interested or no-gold disqualification
- Compliance path: user attempts sensitive sharing (OTP/PAN/CVV)

Artifacts to keep for evaluation:
- CSV row for each scenario
- transcript evidence
- recording URL/local file evidence
- dashboard screenshot(s)

## 11) GitHub Preparation and Upload (Personal Account)

### What was cleaned for repo

- Removed runtime-heavy files like debug logs/backups
- Added `.gitignore` for generated files (`data/calls_data.csv`, recordings, logs, cache)
- Added `data/calls_data.sample.csv` for schema reference

### Option A: HTTPS push

```powershell
cd C:\Users\Manvendra Singh\Desktop\Assessment\vapi_backend
git init
git add .
git commit -m "Initial BFSI gold loan voice agent submission"
git branch -M main
git remote add origin https://github.com/<your-personal-username>/<repo-name>.git
git push -u origin main
```

### Option B: SSH push

```powershell
cd C:\Users\Manvendra Singh\Desktop\Assessment\vapi_backend
git init
git add .
git commit -m "Initial BFSI gold loan voice agent submission"
git branch -M main
git remote add origin git@github.com:<your-personal-username>/<repo-name>.git
git push -u origin main
```

If you have two GitHub accounts, choose personal account at auth prompt (or use personal SSH key/profile).

## 12) Notes

- Keep API keys out of committed files.
- `data/calls_data.csv` is local runtime data; share masked sample data only.
- For strict evaluation, include consent note + voice cloning evidence in repository docs or submission pack.
