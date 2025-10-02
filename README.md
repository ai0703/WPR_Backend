# WPR Backend Ingest Service

Flask backend that accepts analytics payloads identified by a `runId`, stores them in Firebase Realtime Database, and exposes a retrieval endpoint for frontend consumers.

## Requirements

- Python 3.13+
- Firebase project with Realtime Database enabled
- Service account credentials for Firebase Admin SDK

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # on Windows PowerShell
   pip install -r requirements.txt
   ```
2. Copy `config/env.example` to `.env` and populate:
   - `INGEST_TOKEN`: shared secret for ingest and retrieval endpoints
   - `FIREBASE_PROJECT_ID`: Firebase project identifier
   - `FIREBASE_DATABASE_URL`: Realtime Database URL
   - `FIREBASE_CREDENTIALS_JSON_PATH`: path to service account JSON (or `FIREBASE_CREDENTIALS_JSON` inline JSON)

## Running locally

```bash
flask --app app:create_app --debug run
```

The service listens on `http://127.0.0.1:5000` by default.

## API

All endpoints require `Authorization: Bearer <INGEST_TOKEN>` header.

- `POST /api/ingest`
  - Body: `{ "kind": "…", "runId": "…", "payload": { … } }`
  - Stores normalized payload at `runs/<runId>/<kind>`.
  - Response: `{ "ok": true, "kind": "…", "runId": "…" }`

- `GET /api/runs/<runId>`
  - Returns `{ "runId": "…", "data": { <kind>: { … }, … } }`

## Notes

- `app/normalizers.py` mirrors the original JS logic to coerce arrays and JSON-stringified blobs for consistency with existing consumers.
- `config/env.example` documents environment variables and supports both file-path and inline JSON credentials.

