from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import Unauthorized, NotFound, BadRequest

from .models import IngestBody, IngestResponse
from .normalizers import normalize_payload
from .storage import get_run, get_runs_matching_window, upsert_payload


api_bp = Blueprint("api", __name__)


def _require_token(header_value: str | None) -> None:
    token = current_app.config.get("INGEST_TOKEN")
    if not token:
        raise RuntimeError("INGEST_TOKEN is not configured")
    if header_value is None or not header_value.startswith("Bearer "):
        raise Unauthorized("Missing Authorization header")
    provided = header_value.split(" ", 1)[1]
    if provided != token:
        raise Unauthorized("Invalid ingest token")


@api_bp.post("/ingest")
def ingest():
    _require_token(request.headers.get("Authorization"))

    try:
        body = IngestBody.model_validate(request.get_json(force=True))
    except Exception as exc:  # pragma: no cover - delegated to Pydantic
        raise BadRequest(str(exc)) from exc

    run_id = body.runId or body.payload.pop("runId", None)
    if not run_id:
        raise BadRequest("runId is required either at the top level or inside payload")

    normalized_payload = normalize_payload(body.kind, body.payload)
    upsert_payload(run_id, body.kind.value, normalized_payload)

    response = IngestResponse(kind=body.kind, runId=run_id)
    return jsonify(response.model_dump())


@api_bp.get("/runs/<string:run_id>")
def fetch_run_endpoint(run_id: str):
    _require_token(request.headers.get("Authorization"))
    run_data = get_run(run_id)
    if run_data is None:
        raise NotFound(f"Run with id '{run_id}' not found")
    return jsonify({"runId": run_id, "data": run_data})


@api_bp.get("/runs")
def fetch_runs():
    _require_token(request.headers.get("Authorization"))

    since = request.args.get("since")
    until = request.args.get("until")

    # If both since and until are provided, filter by date window
    if since and until:
        try:
            runs = get_runs_matching_window(since, until)
            return jsonify({"since": since, "until": until, "runs": runs})
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
    
    # If no date parameters, return all available runs
    from .storage import get_all_runs
    all_runs = get_all_runs()
    return jsonify({"runs": all_runs})


@api_bp.errorhandler(BadRequest)
def handle_bad_request(err: BadRequest):
    return jsonify({"error": err.description or "Bad request"}), err.code


@api_bp.errorhandler(Unauthorized)
def handle_unauthorized(err: Unauthorized):
    return jsonify({"error": err.description or "Unauthorized"}), err.code


@api_bp.errorhandler(NotFound)
def handle_not_found(err: NotFound):
    return jsonify({"error": err.description or "Not found"}), err.code

