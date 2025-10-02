from __future__ import annotations

import os
from flask import Flask
from dotenv import load_dotenv

from .firebase import init_firebase
from .routes import api_bp


def create_app() -> Flask:
    """Application factory for the ingest service."""

    # Load environment variables from a .env file if present.
    load_dotenv()

    app = Flask(__name__)
    app.config.update(
        {
            "INGEST_TOKEN": os.getenv("INGEST_TOKEN"),
            "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID"),
            "FIREBASE_DATABASE_URL": os.getenv("FIREBASE_DATABASE_URL"),
            "FIREBASE_CREDENTIALS_JSON_PATH": os.getenv("FIREBASE_CREDENTIALS_JSON_PATH"),
            "FIREBASE_CREDENTIALS_JSON": os.getenv("FIREBASE_CREDENTIALS_JSON"),
        }
    )

    # Ensure JSON responses preserve key order (useful for diffing stored payloads).
    app.config.setdefault("JSON_SORT_KEYS", False)

    init_firebase(app)

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/health")
    def health() -> dict[str, str]:  # pragma: no cover - trivial route
        return {"status": "ok"}

    return app

