"""
F1 — Unit tests for P&L Analyzer's _compute_pnl() function.
These tests are pure Python — no DB, no LLM, no network.

Run:
    cd backend && python -m pytest tests/test_pnl.py -v
"""

import pytest
import sys
import os

# Make sure 'backend/' is on the path when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.pnl_analyzer import _compute_pnl


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_tx(amount: float, category: str = "other") -> dict:
    return {"date": "2024-01-01", "description": "test", "amount": amount, "category": category}


# ── Test cases ────────────────────────────────────────────────────────────────

class TestComputePnl:

    def test_basic_revenue_and_expenses(self):
        """Basic case: mixed positive (revenue) and negative (expense) transactions."""
        txns = [
            make_tx(10000, "revenue"),
            make_tx(5000,  "revenue"),
            make_tx(-3000, "expense"),
            make_tx(-2000, "expense"),
        ]
        result = _compute_pnl(txns)

        assert result["revenue"] == 15000.0
        assert result["expenses"] == 5000.0
        assert result["gross_profit"] == 10000.0
        assert result["gross_margin_pct"] == pytest.approx(66.67, abs=0.1)
        # Net profit should be gross * (1 - TAX_RATE) — default 25%
        assert result["net_profit"] == pytest.approx(7500.0, abs=1.0)
        # Category breakdown
        assert "revenue" in result["by_category"]
        assert "expense" in result["by_category"]
        assert result["by_category"]["revenue"] == pytest.approx(15000.0)
        assert result["by_category"]["expense"] == pytest.approx(-5000.0)

    def test_zero_revenue(self):
        """Edge case: all expenses, no revenue — gross profit is negative."""
        txns = [
            make_tx(-1000, "expense"),
            make_tx(-2000, "expense"),
        ]
        result = _compute_pnl(txns)

        assert result["revenue"] == 0.0
        assert result["expenses"] == 3000.0
        assert result["gross_profit"] == -3000.0
        # When gross_profit <= 0, net_profit should equal gross_profit (no tax on loss)
        assert result["net_profit"] == -3000.0
        # Margin is 0 when revenue is 0
        assert result["gross_margin_pct"] == 0.0

    def test_all_revenue(self):
        """Edge case: all revenue, no expenses — 100% gross margin."""
        txns = [
            make_tx(5000,  "revenue"),
            make_tx(10000, "saas"),
        ]
        result = _compute_pnl(txns)

        assert result["revenue"] == 15000.0
        assert result["expenses"] == 0.0
        assert result["gross_profit"] == 15000.0
        assert result["gross_margin_pct"] == 100.0
        # Net profit should reflect tax deduction
        assert result["net_profit"] < result["gross_profit"]
        assert result["net_profit"] == pytest.approx(11250.0, abs=1.0)

    def test_empty_transactions(self):
        """Empty list — all values should be zero, no crash."""
        result = _compute_pnl([])

        assert result["revenue"] == 0.0
        assert result["expenses"] == 0.0
        assert result["gross_profit"] == 0.0
        assert result["net_profit"] == 0.0
        assert result["gross_margin_pct"] == 0.0
        assert result["by_category"] == {}

    def test_single_transaction_revenue(self):
        """Single transaction — should not crash."""
        result = _compute_pnl([make_tx(1000, "revenue")])

        assert result["revenue"] == 1000.0
        assert result["expenses"] == 0.0

    def test_category_aggregation(self):
        """Multiple transactions in same category should aggregate correctly."""
        txns = [
            make_tx(1000, "saas"),
            make_tx(2000, "saas"),
            make_tx(-500, "aws"),
            make_tx(-500, "aws"),
        ]
        result = _compute_pnl(txns)

        assert result["by_category"]["saas"] == pytest.approx(3000.0)
        assert result["by_category"]["aws"] == pytest.approx(-1000.0)
