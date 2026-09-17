"""Local AQIS API and frontend server.

This dependency-free server exposes the project's precomputed model outputs to
the connected frontend. It intentionally keeps live inference separate: the
existing ML pipeline can be mounted behind the same endpoints later.
"""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import re
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = PROJECT_ROOT / "stitch_aqis_air_quality_dashboard" / "simplified_frontend"
DEMO_ROOT = PROJECT_ROOT / "data" / "demo"
RUNTIME_ROOT = PROJECT_ROOT / "runtime"


def safe_city(value: str) -> str:
    city = value.lower().strip()
    return city if city in {"mumbai", "delhi"} else "mumbai"


def station_records(city: str) -> list[dict]:
    records = []
    folder = DEMO_ROOT / safe_city(city)
    for path in sorted(folder.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records.append(
            {
                "id": path.stem,
                "name": payload.get("location", path.stem.replace("_", " ")),
                "latitude": payload.get("latitude"),
                "longitude": payload.get("longitude"),
                "timestamp": payload.get("timestamp"),
            }
        )
    return records


def station_payload(city: str, station_id: str | None) -> dict | None:
    folder = DEMO_ROOT / safe_city(city)
    candidates = sorted(folder.glob("*.json"))
    if not candidates:
        return None
    selected = None
    if station_id:
        normalized = re.sub(r"[^a-z0-9]", "", station_id.lower())
        for path in candidates:
            stem = re.sub(r"[^a-z0-9]", "", path.stem.lower())
            if normalized in stem or stem in normalized:
                selected = path
                break
    if selected is None:
        selected = next((path for path in candidates if "borivali" in path.stem.lower()), candidates[0])
    try:
        return json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def model_metrics() -> dict:
    sources = {
        "baseline": PROJECT_ROOT / "reports" / "figures" / "xgboost_metrics.csv",
        "tuned": PROJECT_ROOT / "reports" / "figures" / "xgboost_tuned_metrics.csv",
    }
    output = {}
    for name, path in sources.items():
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                output[name] = next(csv.DictReader(handle))
        except (OSError, StopIteration):
            output[name] = None
    return output


class AQISHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/api/health":
            return self.send_json(
                {
                    "status": "ok",
                    "mode": "precomputed-model-cache",
                    "cities": ["mumbai", "delhi"],
                    "server_time": datetime.now(timezone.utc).isoformat(),
                }
            )
        if parsed.path == "/api/stations":
            city = safe_city(query.get("city", ["mumbai"])[0])
            return self.send_json({"city": city, "stations": station_records(city)})
        if parsed.path == "/api/intelligence":
            city = safe_city(query.get("city", ["mumbai"])[0])
            station_id = query.get("station", [None])[0]
            payload = station_payload(city, station_id)
            if payload is None:
                return self.send_json({"error": "No cached station intelligence found."}, HTTPStatus.NOT_FOUND)
            return self.send_json({"mode": "precomputed", "city": city, "data": payload})
        if parsed.path == "/api/model/metrics":
            return self.send_json({"model": "xgboost", "metrics": model_metrics()})
        if parsed.path == "/":
            self.path = "/landing.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/reports", "/api/alerts"}:
            return self.send_json({"error": "Unknown endpoint."}, HTTPStatus.NOT_FOUND)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return self.send_json({"error": "Invalid JSON body."}, HTTPStatus.BAD_REQUEST)
        kind = "reports" if parsed.path.endswith("reports") else "alerts"
        target = RUNTIME_ROOT / kind
        target.mkdir(parents=True, exist_ok=True)
        record_id = f"AQIS-{kind[:-1].upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
        record = {"id": record_id, "created_at": datetime.now(timezone.utc).isoformat(), "payload": body}
        (target / f"{record_id}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.send_json(record, HTTPStatus.CREATED)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the AQIS frontend and local API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    mimetypes.add_type("text/javascript", ".js")
    server = ThreadingHTTPServer((args.host, args.port), AQISHandler)
    print(f"AQIS available at http://{args.host}:{args.port}/")
    print("API mode: precomputed model cache")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
