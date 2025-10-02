from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, db
from flask import Flask


class FirebaseNotConfigured(RuntimeError):
    """Raised when required Firebase configuration values are missing."""


_FIREBASE_APP: firebase_admin.App | None = None


def init_firebase(app: Flask) -> None:
    """Initialise the Firebase Admin SDK using app configuration."""

    global _FIREBASE_APP

    if _FIREBASE_APP is not None:
        return

    project_id = app.config.get("FIREBASE_PROJECT_ID")
    database_url = app.config.get("FIREBASE_DATABASE_URL")
    credentials_path = app.config.get("FIREBASE_CREDENTIALS_JSON_PATH")
    credentials_json = app.config.get("FIREBASE_CREDENTIALS_JSON")

    if not project_id or not database_url:
        raise FirebaseNotConfigured(
            "FIREBASE_PROJECT_ID and FIREBASE_DATABASE_URL must be configured"
        )

    cred: credentials.Base
    if credentials_json:
        # Prioritize JSON string over file path for deployment
        cred = credentials.Certificate(json.loads(credentials_json))
    elif credentials_path:
        cred = credentials.Certificate(_load_credentials(credentials_path))
    else:
        cred = credentials.ApplicationDefault()

    _FIREBASE_APP = firebase_admin.initialize_app(
        cred,
        {
            "projectId": project_id,
            "databaseURL": database_url,
        },
    )


def _load_credentials(path: str) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Firebase credential file not found at {resolved}")
    return json.loads(resolved.read_text())


def get_db_root() -> db.Reference:
    if _FIREBASE_APP is None:
        raise FirebaseNotConfigured("Firebase has not been initialised")
    return db.reference("runs", app=_FIREBASE_APP)


def write_payload(run_id: str, kind: str, payload: dict[str, Any]) -> None:
    """Write a payload under runs/<run_id>/<kind>."""

    get_db_root().child(run_id).child(kind).set(payload)


def fetch_run(run_id: str) -> dict[str, Any] | None:
    """Fetch all payloads stored for a run id."""

    data = get_db_root().child(run_id).get()
    if data is None:
        return None
    if isinstance(data, dict):
        return data
    raise TypeError("Unexpected data type returned from Firebase Realtime Database")


def fetch_all_runs() -> dict[str, Any]:
    """Fetch every run stored in Firebase."""

    data = get_db_root().get()
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    raise TypeError("Unexpected data type returned from Firebase Realtime Database")

