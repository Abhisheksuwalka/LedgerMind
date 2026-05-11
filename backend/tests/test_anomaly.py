"""
F2 — Unit tests for Anomaly Detection's _zscore_anomalies() function.
Pure Python — no DB, no LLM, no network.

Run:
    cd backend && python -m pytest tests/test_anomaly.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.anomaly_detection import _zscore_anomalies


def make_tx(amount: float, description: str = "tx", date: str = "2024-01-01") -> dict:
    return {"date": date, "description": description, "amount": amount, "category": "other"}


class TestZscoreAnomalies:

    def test_detects_clear_outlier(self):
        """A single extreme transaction should be flagged as anomalous."""
        # 9 normal transactions around $100, 1 massive outlier at $10,000
        txns = [make_tx(100 + i) for i in range(9)]
        txns.append(make_tx(10000, "Huge payment"))

        flagged = _zscore_anomalies(txns)

        assert len(flagged) >= 1
        # The outlier should be in the flagged list
        flagged_amounts = [f["transaction"]["amount"] for f in flagged]
        assert 10000 in flagged_amounts

    def test_uniform_data_no_anomalies(self):
        """Identical amounts have std=0 — function must return empty list, not crash."""
        txns = [make_tx(500) for _ in range(10)]

        flagged = _zscore_anomalies(txns)

        # std=0 → division guard triggers → no anomalies
        assert flagged == []

    def test_too_few_rows_returns_empty(self):
        """Fewer than 4 transactions — function skips analysis and returns []."""
        txns = [make_tx(100), make_tx(200), make_tx(300)]

        flagged = _zscore_anomalies(txns)

        assert flagged == []

    def test_negative_outlier_flagged(self):
        """Large negative expense should be flagged (e.g. fraud payment)."""
        txns = [make_tx(-100) for _ in range(9)]
        txns.append(make_tx(-50000, "Suspicious large debit"))

        flagged = _zscore_anomalies(txns)

        assert len(flagged) >= 1
        amounts = [f["transaction"]["amount"] for f in flagged]
        assert -50000 in amounts

    def test_duplicate_detection(self):
        """Same amount + description within 3 days should flag as potential duplicate."""
        txns = [make_tx(100 + i) for i in range(8)]  # background noise
        txns.append(make_tx(105.50, "Duplicate Payment", "2024-01-10"))
        txns.append(make_tx(105.50, "Duplicate Payment", "2024-01-11"))

        flagged = _zscore_anomalies(txns)

        # At least one of the duplicates should be flagged
        reason_hints = [f.get("reason_hint", "") for f in flagged]
        assert "potential_duplicate" in reason_hints

    def test_anomaly_score_bounded(self):
        """anomaly_score should never exceed 1.0."""
        txns = [make_tx(10 + i) for i in range(9)]
        txns.append(make_tx(1_000_000))

        flagged = _zscore_anomalies(txns)

        for item in flagged:
            assert item["anomaly_score"] <= 1.0
            assert item["anomaly_score"] >= 0.0
