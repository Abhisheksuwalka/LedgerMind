"""
F5 — Integration test: uploads sample_transactions.csv, polls for completion,
verifies a report was created in the DB.

Requires the full stack running:
    docker compose up --build

Then run from project root:
    cd backend && python -m pytest tests/test_integration.py -v --timeout=120

Skip if backend is unavailable (CI-friendly).
"""

import os
import time
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = os.getenv("TEST_API_BASE_URL", "http://localhost:8000")
SAMPLE_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sample_transactions.csv",
)
MAX_WAIT_SECONDS = 90
POLL_INTERVAL = 3


def _api_available() -> bool:
    try:
        import requests
        r = requests.get(f"{API_BASE}/health", timeout=3)
        if r.status_code == 200:
            return r.json().get("service") == "LedgerMind"
        return False
    except Exception:
        return False


@pytest.mark.skipif(
    not _api_available(),
    reason="Backend not running — start with 'docker compose up' before integration tests",
)
class TestEndToEndPipeline:

    def test_upload_csv_returns_202(self):
        """POST /api/v1/run with sample CSV should return 202 Accepted with a run_id."""
        import requests

        assert os.path.exists(SAMPLE_CSV), f"sample_transactions.csv not found at {SAMPLE_CSV}"

        with open(SAMPLE_CSV, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/api/v1/run",
                files={"file": ("sample_transactions.csv", f, "text/csv")},
                data={"file_type": "csv", "triggered_by": "integration_test"},
                headers={"x-api-key": os.getenv("API_KEY", "")},
                timeout=30,
            )

        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "run_id" in body
        assert body["status"] == "accepted"

    def test_full_pipeline_completes_and_report_exists(self):
        """Full pipeline test: upload → poll → verify completed → check report exists."""
        import requests

        # 1. Upload
        with open(SAMPLE_CSV, "rb") as f:
            run_resp = requests.post(
                f"{API_BASE}/api/v1/run",
                files={"file": ("sample_transactions.csv", f, "text/csv")},
                data={"file_type": "csv", "triggered_by": "integration_test"},
                headers={"x-api-key": os.getenv("API_KEY", "")},
                timeout=30,
            )
        assert run_resp.status_code == 202
        run_id = run_resp.json()["run_id"]

        # 2. Poll until completed or timeout
        deadline = time.time() + MAX_WAIT_SECONDS
        final_status = None
        while time.time() < deadline:
            status_resp = requests.get(
                f"{API_BASE}/api/v1/runs/{run_id}/status", timeout=10
            )
            assert status_resp.status_code == 200
            data = status_resp.json()
            final_status = data["status"]

            if final_status in ("completed", "failed"):
                break
            time.sleep(POLL_INTERVAL)

        assert final_status == "completed", (
            f"Pipeline did not complete within {MAX_WAIT_SECONDS}s. "
            f"Last status: {final_status}"
        )

        # 3. Verify a report was stored
        reports_resp = requests.get(f"{API_BASE}/api/v1/reports", timeout=10)
        assert reports_resp.status_code == 200
        reports = reports_resp.json()
        assert len(reports) >= 1, "No reports found after pipeline completed"

        # Find report for this run
        matching = [r for r in reports if r.get("run_id") == run_id]
        assert len(matching) >= 1, f"No report found for run_id={run_id}"

        # 4. Fetch full report and verify markdown content
        report_id = matching[0]["id"]
        detail_resp = requests.get(f"{API_BASE}/api/v1/reports/{report_id}", timeout=10)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        assert detail.get("markdown_report"), "markdown_report is empty"
        assert "LedgerMind" in detail["markdown_report"], (
            "Report should reference LedgerMind in content"
        )

    def test_audit_trail_exists_after_run(self):
        """After a completed run, audit trail should have entries."""
        import requests

        with open(SAMPLE_CSV, "rb") as f:
            run_resp = requests.post(
                f"{API_BASE}/api/v1/run",
                files={"file": ("sample_transactions.csv", f, "text/csv")},
                data={"file_type": "csv", "triggered_by": "integration_test_audit"},
                headers={"x-api-key": os.getenv("API_KEY", "")},
                timeout=30,
            )
        run_id = run_resp.json()["run_id"]

        # Wait for completion
        deadline = time.time() + MAX_WAIT_SECONDS
        while time.time() < deadline:
            s = requests.get(f"{API_BASE}/api/v1/runs/{run_id}/status", timeout=10).json()
            if s["status"] in ("completed", "failed"):
                break
            time.sleep(POLL_INTERVAL)

        audit_resp = requests.get(f"{API_BASE}/api/v1/audit/{run_id}", timeout=10)
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        assert len(logs) >= 1, "No audit entries found for run"

    def test_invalid_file_returns_400(self):
        """Empty file should return 400 Bad Request."""
        import requests

        resp = requests.post(
            f"{API_BASE}/api/v1/run",
            files={"file": ("empty.csv", b"", "text/csv")},
            data={"file_type": "csv"},
            headers={"x-api-key": os.getenv("API_KEY", ""), "X-Forwarded-For": "192.168.1.100"},
            timeout=10,
        )
        assert resp.status_code in (400, 429), "Expected 400 for empty file, or 429 if rate limited"

    def test_settings_endpoint_returns_providers(self):
        """GET /api/v1/settings should return provider configuration."""
        import requests

        resp = requests.get(f"{API_BASE}/api/v1/settings", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert "groq" in data["providers"]
        assert "gemini" in data["providers"]
        assert "anthropic" in data["providers"]
        assert "tax_rate_pct" in data
