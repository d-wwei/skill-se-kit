"""HTTP sidecar server for Skill-SE-Kit.

Provides a localhost HTTP API that wraps SkillRuntime, eliminating
subprocess-per-call overhead for cross-language integrations.

Usage::

    skill-se-kit serve --skill-root /path/to/skill --port 9780

Endpoints::

    GET  /health       — version and status
    POST /run          — execute + learn (body: {input, context?, feedback?})
    GET  /skills       — current skill bank
    GET  /report       — latest evolution summary (text)
    GET  /report/json  — latest evolution report (JSON)
    POST /rollback     — revert to snapshot (body: {snapshot_id})
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from skill_se_kit import __version__
from skill_se_kit.common import load_json
from skill_se_kit.runtime.skill_runtime import SkillRuntime


class _Handler(BaseHTTPRequestHandler):
    """HTTP request handler backed by a shared SkillRuntime instance."""

    runtime: SkillRuntime  # set by serve()

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        if path == "/health" or path == "":
            self._handle_health()
        elif path == "/skills":
            self._handle_skills()
        elif path == "/report":
            self._handle_report_text()
        elif path == "/report/json":
            self._handle_report_json()
        else:
            self._send_error(404, f"Not found: {path}")

    def do_POST(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        if path == "/run":
            self._handle_run()
        elif path == "/rollback":
            self._handle_rollback()
        else:
            self._send_error(404, f"Not found: {path}")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_health(self) -> None:
        self._send_json(200, {
            "ok": True,
            "data": {
                "version": __version__,
                "skill_root": str(self.runtime.workspace.root),
                "status": "running",
            },
        })

    def _handle_run(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        input_data = body.get("input")
        if not input_data:
            self._send_error(400, "Missing required field: input")
            return
        try:
            result = self.runtime.run_integrated_skill(
                input_data,
                context=body.get("context"),
                feedback=body.get("feedback"),
                auto_promote=body.get("auto_promote"),
                run_mode=body.get("run_mode"),
            )
            self._send_json(200, {"ok": True, "data": result})
        except Exception as exc:
            self._send_error(500, str(exc))

    def _handle_skills(self) -> None:
        try:
            skills_path = self.runtime.workspace.local_skill_bank_path
            if skills_path.exists():
                bank = load_json(skills_path)
            else:
                bank = {"skills": []}
            self._send_json(200, {"ok": True, "data": bank})
        except Exception as exc:
            self._send_error(500, str(exc))

    def _handle_report_text(self) -> None:
        try:
            summary = self.runtime.get_latest_evolution_summary()
            self._send_json(200, {
                "ok": True,
                "data": {"text": summary or "No evolution report is available yet."},
            })
        except Exception as exc:
            self._send_error(500, str(exc))

    def _handle_report_json(self) -> None:
        try:
            report = self.runtime.get_latest_evolution_report()
            self._send_json(200, {
                "ok": True,
                "data": report or {"status": "no_report"},
            })
        except Exception as exc:
            self._send_error(500, str(exc))

    def _handle_rollback(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        snapshot_id = body.get("snapshot_id")
        if not snapshot_id:
            self._send_error(400, "Missing required field: snapshot_id")
            return
        try:
            result = self.runtime.rollback(snapshot_id)
            self._send_json(200, {"ok": True, "data": result})
        except Exception as exc:
            self._send_error(500, str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._send_error(400, "Empty request body")
            return None
        try:
            raw = self.rfile.read(length)
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._send_error(400, f"Invalid JSON: {exc}")
            return None

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str) -> None:
        self._send_json(status, {"ok": False, "error": message})

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write(f"[skill-se-kit] {args[0]} {args[1]} {args[2]}\n")


def serve(runtime: SkillRuntime, *, host: str = "127.0.0.1", port: int = 9780) -> None:
    """Start the HTTP sidecar server.

    Blocks until interrupted (Ctrl+C).
    """
    _Handler.runtime = runtime

    server = ThreadingHTTPServer((host, port), _Handler)
    banner = (
        f"\n  skill-se-kit serve v{__version__}\n"
        f"  Listening on http://{host}:{port}\n"
        f"  Skill root: {runtime.workspace.root}\n"
        f"\n"
        f"  Endpoints:\n"
        f"    GET  /health       — version and status\n"
        f"    POST /run          — execute + learn\n"
        f"    GET  /skills       — current skill bank\n"
        f"    GET  /report       — evolution summary (text)\n"
        f"    GET  /report/json  — evolution report (JSON)\n"
        f"    POST /rollback     — revert to snapshot\n"
        f"\n"
        f"  Press Ctrl+C to stop.\n"
    )
    print(banner, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
    finally:
        server.server_close()
