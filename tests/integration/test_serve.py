"""Integration tests for the HTTP sidecar server."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ROOT = REPO_ROOT.parent / "skill-evolution-protocol"


def _skip_if_no_protocol() -> bool:
    return not PROTOCOL_ROOT.exists()


class TestServe(unittest.TestCase):
    """Test the HTTP sidecar server endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        if _skip_if_no_protocol():
            raise unittest.SkipTest("skill-evolution-protocol not found")

        cls._tmpdir = tempfile.TemporaryDirectory()
        cls._skill_root = Path(cls._tmpdir.name) / "test-skill"
        cls._skill_root.mkdir()

        # Bootstrap via CLI init
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skill_se_kit",
                "init",
                "--skill-root",
                str(cls._skill_root),
                "--protocol-root",
                str(PROTOCOL_ROOT),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        )
        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Start server in background thread
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from skill_se_kit.runtime.skill_runtime import SkillRuntime
        from skill_se_kit.serve import serve

        cls._runtime = SkillRuntime.from_auto_integration(cls._skill_root)
        cls._port = 19780  # use non-default port for tests
        cls._server_thread = threading.Thread(
            target=serve,
            kwargs={"runtime": cls._runtime, "port": cls._port},
            daemon=True,
        )
        cls._server_thread.start()
        # Wait for server to start
        for _ in range(20):
            try:
                conn = HTTPConnection("127.0.0.1", cls._port, timeout=1)
                conn.request("GET", "/health")
                conn.getresponse()
                conn.close()
                break
            except (ConnectionRefusedError, OSError):
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()

    def _request(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self._port, timeout=10)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            conn.request(method, path, body=data, headers={"Content-Type": "application/json"})
        else:
            conn.request(method, path)
        resp = conn.getresponse()
        status = resp.status
        payload = json.loads(resp.read())
        conn.close()
        return status, payload

    def test_health(self) -> None:
        status, payload = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertIn("version", payload["data"])
        self.assertEqual(payload["data"]["status"], "running")

    def test_run(self) -> None:
        status, payload = self._request("POST", "/run", {
            "input": {"task": "test-task", "user_input": "Always be concise."},
            "feedback": {
                "status": "positive",
                "lesson": "Keep responses short.",
                "source": "explicit",
                "confidence": 0.9,
            },
        })
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["data"]["kit_active"])

    def test_run_missing_input(self) -> None:
        status, payload = self._request("POST", "/run", {"context": {}})
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])

    def test_skills(self) -> None:
        status, payload = self._request("GET", "/skills")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertIn("skills", payload["data"])

    def test_report_text(self) -> None:
        status, payload = self._request("GET", "/report")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertIn("text", payload["data"])

    def test_report_json(self) -> None:
        status, payload = self._request("GET", "/report/json")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])

    def test_not_found(self) -> None:
        status, payload = self._request("GET", "/nonexistent")
        self.assertEqual(status, 404)
        self.assertFalse(payload["ok"])

    def test_cors_headers(self) -> None:
        conn = HTTPConnection("127.0.0.1", self._port, timeout=10)
        conn.request("OPTIONS", "/run")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 204)
        self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), "*")
        conn.close()


if __name__ == "__main__":
    unittest.main()
