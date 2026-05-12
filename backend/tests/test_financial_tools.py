"""
test_financial_tools.py — Phase 3 unit tests
=============================================
Tests all 6 financial tools and the period parser with mock data.
Uses pytest-asyncio + unittest.mock to avoid any real DB or LLM calls.

Run:
    docker compose exec backend python -m pytest tests/test_financial_tools.py -v
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import UUID, uuid4

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════════════════════
# Period Parser Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPeriodParser:
    """Test parse_period() for all supported format strings."""

    def setup_method(self):
        from tools.period_parser import parse_period
        self.parse = parse_period

    def test_last_30d_returns_30_day_window(self):
        start, end = self.parse("last_30d")
        delta = end - start
        assert 29 <= delta.days <= 31

    def test_last_7d(self):
        start, end = self.parse("last_7d")
        assert 6 <= (end - start).days <= 8

    def test_last_90d(self):
        start, end = self.parse("last_90d")
        assert 89 <= (end - start).days <= 91

    def test_this_month_starts_on_1st(self):
        start, end = self.parse("this_month")
        assert start.day == 1
        assert start.hour == 0 and start.minute == 0

    def test_last_month_full_calendar_month(self):
        start, end = self.parse("last_month")
        # start must be the 1st of last month
        assert start.day == 1
        # end must be the last day of that same month (at least the 28th)
        assert end.day >= 28
        # start and end are in the same month (e.g. April 1 → April 30)
        assert start.month == end.month
        # and that month is in the past relative to today
        now = datetime.now(timezone.utc)
        assert start.month != now.month or start.year != now.year

    def test_this_quarter_starts_on_1st_of_quarter_month(self):
        start, end = self.parse("this_quarter")
        assert start.month in (1, 4, 7, 10)
        assert start.day == 1

    def test_last_quarter_is_3_months(self):
        start, end = self.parse("last_quarter")
        months = (end.year - start.year) * 12 + (end.month - start.month)
        assert months == 2   # 3 months span = month_end - month_start = 2

    def test_ytd_starts_jan_1(self):
        start, end = self.parse("ytd")
        assert start.month == 1 and start.day == 1

    def test_specific_quarter_2024_q1(self):
        start, end = self.parse("2024-Q1")
        assert start.year == 2024 and start.month == 1 and start.day == 1
        assert end.month == 3

    def test_specific_quarter_2024_q4(self):
        start, end = self.parse("2024-Q4")
        assert start.month == 10 and end.month == 12

    def test_specific_month_2024_06(self):
        start, end = self.parse("2024-06")
        assert start.year == 2024 and start.month == 6 and start.day == 1
        assert end.month == 6

    def test_explicit_range(self):
        start, end = self.parse("2024-01-15:2024-03-31")
        assert start.day == 15 and start.month == 1
        assert end.month == 3 and end.day == 31

    def test_unknown_period_raises_value_error(self):
        with pytest.raises(ValueError, match="Unrecognised period"):
            self.parse("this_decade")

    def test_all_formats_return_aware_datetimes(self):
        for period in ["last_30d", "this_month", "last_month", "this_quarter",
                       "last_quarter", "ytd", "2024-Q2", "2024-03"]:
            start, end = self.parse(period)
            assert start.tzinfo is not None, f"start has no tzinfo for {period}"
            assert end.tzinfo is not None, f"end has no tzinfo for {period}"

    def test_start_before_end_always(self):
        for period in ["last_30d", "last_7d", "this_month", "last_month",
                       "this_quarter", "last_quarter", "ytd",
                       "2024-Q1", "2024-01", "2023-12"]:
            start, end = self.parse(period)
            assert start <= end, f"start > end for period {period}"


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — mock Transaction row builder
# ═══════════════════════════════════════════════════════════════════════════════

def _make_tx(amount: float, category: str = "expense", days_ago: int = 5,
             description: str = "Test transaction", currency: str = "USD") -> MagicMock:
    tx = MagicMock()
    tx.id = uuid4()
    tx.amount = amount
    tx.category = category
    tx.date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    tx.description = description
    tx.currency = currency
    tx.is_anomaly = False
    tx.anomaly_score = None
    return tx


def _mock_db(txns: list) -> AsyncMock:
    """Build a mock AsyncSession whose execute() returns the given transaction list."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = txns

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)
    return db


BUSINESS_ID = uuid4()


# ═══════════════════════════════════════════════════════════════════════════════
# compute_pnl
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputePnlTool:

    @pytest.mark.asyncio
    async def test_basic_revenue_and_expenses(self):
        from tools.financial_tools import compute_pnl
        txns = [
            _make_tx(1000.0, "revenue"),   # +
            _make_tx(-400.0, "expense"),   # -
            _make_tx(-100.0, "expense"),   # -
        ]
        result = await compute_pnl(_mock_db(txns), BUSINESS_ID, "last_30d")
        assert result["revenue"] == pytest.approx(1000.0)
        assert result["expenses"] == pytest.approx(500.0)
        assert result["gross_profit"] == pytest.approx(500.0)
        assert result["margin_pct"] == pytest.approx(50.0)
        assert result["transaction_count"] == 3

    @pytest.mark.asyncio
    async def test_zero_revenue_margin_is_zero(self):
        from tools.financial_tools import compute_pnl
        txns = [_make_tx(-500.0, "expense")]
        result = await compute_pnl(_mock_db(txns), BUSINESS_ID)
        assert result["revenue"] == 0.0
        assert result["margin_pct"] == 0.0
        assert result["expenses"] == pytest.approx(500.0)

    @pytest.mark.asyncio
    async def test_empty_transactions(self):
        from tools.financial_tools import compute_pnl
        result = await compute_pnl(_mock_db([]), BUSINESS_ID)
        assert result["revenue"] == 0.0
        assert result["expenses"] == 0.0
        assert result["transaction_count"] == 0

    @pytest.mark.asyncio
    async def test_period_metadata_present(self):
        from tools.financial_tools import compute_pnl
        result = await compute_pnl(_mock_db([]), BUSINESS_ID, "last_7d")
        assert "period_start" in result
        assert "period_end" in result
        assert result["period"] == "last_7d"

    @pytest.mark.asyncio
    async def test_category_breakdown(self):
        from tools.financial_tools import compute_pnl
        txns = [
            _make_tx(200.0, "sales"),
            _make_tx(300.0, "services"),
            _make_tx(-150.0, "rent"),
            _make_tx(-50.0, "utilities"),
        ]
        result = await compute_pnl(_mock_db(txns), BUSINESS_ID)
        assert "revenue_by_category" in result
        assert "expenses_by_category" in result
        assert result["revenue_by_category"].get("sales") == pytest.approx(200.0)
        assert result["expenses_by_category"].get("rent") == pytest.approx(150.0)


# ═══════════════════════════════════════════════════════════════════════════════
# compute_runway
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputeRunway:

    @pytest.mark.asyncio
    async def test_no_data_returns_warning(self):
        from tools.financial_tools import compute_runway
        result = await compute_runway(_mock_db([]), BUSINESS_ID)
        assert result["warning"] is not None
        assert result["months_of_runway"] is None

    @pytest.mark.asyncio
    async def test_positive_revenue_above_burn(self):
        from tools.financial_tools import compute_runway
        # Revenue > expenses → no burn, runway should be None or very high
        txns = [_make_tx(5000.0, "revenue", days_ago=i) for i in range(1, 15)]
        result = await compute_runway(_mock_db(txns), BUSINESS_ID)
        # net_burn should be 0 → months_of_runway is None (no burn)
        assert result["net_burn"] == 0.0

    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        from tools.financial_tools import compute_runway
        result = await compute_runway(_mock_db([]), BUSINESS_ID)
        for key in ["months_of_runway", "monthly_burn", "monthly_revenue",
                    "net_burn", "warning", "cash_balance_estimate"]:
            assert key in result, f"Missing key: {key}"


# ═══════════════════════════════════════════════════════════════════════════════
# query_transactions
# ═══════════════════════════════════════════════════════════════════════════════

class TestQueryTransactions:

    @pytest.mark.asyncio
    async def test_returns_list_by_default(self):
        from tools.financial_tools import query_transactions
        txns = [_make_tx(100.0), _make_tx(200.0), _make_tx(50.0)]
        result = await query_transactions(_mock_db(txns), BUSINESS_ID)
        assert "transactions" in result
        assert result["total"] == 3

    @pytest.mark.asyncio
    async def test_aggregate_count(self):
        from tools.financial_tools import query_transactions
        txns = [_make_tx(100.0)] * 5
        result = await query_transactions(_mock_db(txns), BUSINESS_ID, aggregate="count")
        assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_aggregate_sum(self):
        from tools.financial_tools import query_transactions
        txns = [_make_tx(100.0), _make_tx(200.0), _make_tx(50.0)]
        result = await query_transactions(_mock_db(txns), BUSINESS_ID, aggregate="sum")
        assert result["sum"] == pytest.approx(350.0)

    @pytest.mark.asyncio
    async def test_aggregate_avg(self):
        from tools.financial_tools import query_transactions
        txns = [_make_tx(100.0), _make_tx(200.0)]
        result = await query_transactions(_mock_db(txns), BUSINESS_ID, aggregate="avg")
        assert result["avg_amount"] == pytest.approx(150.0)

    @pytest.mark.asyncio
    async def test_group_by_category(self):
        from tools.financial_tools import query_transactions
        txns = [
            _make_tx(100.0, "rent"),
            _make_tx(50.0, "rent"),
            _make_tx(200.0, "salary"),
        ]
        result = await query_transactions(_mock_db(txns), BUSINESS_ID,
                                          aggregate="sum", group_by="category")
        assert result["group_by"] == "category"
        assert result["data"]["rent"] == pytest.approx(150.0)
        assert result["data"]["salary"] == pytest.approx(200.0)

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self):
        from tools.financial_tools import query_transactions
        result = await query_transactions(_mock_db([]), BUSINESS_ID)
        assert result["transactions"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_limit_respected(self):
        from tools.financial_tools import query_transactions
        txns = [_make_tx(float(i)) for i in range(50)]
        result = await query_transactions(_mock_db(txns), BUSINESS_ID, limit=10)
        assert len(result["transactions"]) <= 10


# ═══════════════════════════════════════════════════════════════════════════════
# compare_periods
# ═══════════════════════════════════════════════════════════════════════════════

class TestComparePeriods:

    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        from tools.financial_tools import compare_periods
        txns = [_make_tx(500.0, "revenue")]
        result = await compare_periods(_mock_db(txns), BUSINESS_ID)
        for key in ["metric", "period_a", "period_b", "period_a_value",
                    "period_b_value", "change_abs", "change_pct", "interpretation"]:
            assert key in result, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_interpretation_is_string(self):
        from tools.financial_tools import compare_periods
        result = await compare_periods(_mock_db([]), BUSINESS_ID)
        assert isinstance(result["interpretation"], str)
        assert len(result["interpretation"]) > 0

    @pytest.mark.asyncio
    async def test_no_base_period_data_change_pct_is_none(self):
        from tools.financial_tools import compare_periods
        result = await compare_periods(_mock_db([]), BUSINESS_ID,
                                       metric="revenue")
        # Both periods have 0 revenue → change_pct is None
        assert result["change_pct"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# find_anomalies
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindAnomalies:

    @pytest.mark.asyncio
    async def test_detects_clear_outlier(self):
        from tools.financial_tools import find_anomalies
        # 10 normal transactions + 1 massive outlier
        txns = [_make_tx(-50.0) for _ in range(10)]
        txns.append(_make_tx(-5000.0, description="Massive outlier"))
        result = await find_anomalies(_mock_db(txns), BUSINESS_ID,
                                      use_baselines=False)
        assert result["total_flagged"] >= 1
        assert result["method_used"] == "global_zscore"

    @pytest.mark.asyncio
    async def test_uniform_data_no_anomalies(self):
        from tools.financial_tools import find_anomalies
        txns = [_make_tx(-100.0) for _ in range(20)]
        result = await find_anomalies(_mock_db(txns), BUSINESS_ID,
                                      use_baselines=False)
        assert result["total_flagged"] == 0

    @pytest.mark.asyncio
    async def test_too_few_rows_returns_empty(self):
        from tools.financial_tools import find_anomalies
        txns = [_make_tx(-100.0), _make_tx(-200.0)]
        result = await find_anomalies(_mock_db(txns), BUSINESS_ID,
                                      use_baselines=False)
        assert result["total_flagged"] == 0
        assert "insufficient_data" in result["method_used"]

    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        from tools.financial_tools import find_anomalies
        result = await find_anomalies(_mock_db([]), BUSINESS_ID)
        for key in ["anomalies", "total_flagged", "method_used"]:
            assert key in result

    @pytest.mark.asyncio
    async def test_no_business_id_falls_back_to_zscore(self):
        from tools.financial_tools import find_anomalies
        txns = [_make_tx(-50.0) for _ in range(10)]
        txns.append(_make_tx(-9999.0))
        result = await find_anomalies(_mock_db(txns), business_id=None,
                                      use_baselines=True)
        # No business_id → can't use baselines → falls back to global Z-score
        assert result["method_used"] == "global_zscore"


# ═══════════════════════════════════════════════════════════════════════════════
# get_category_trends
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetCategoryTrends:

    @pytest.mark.asyncio
    async def test_returns_trends_list(self):
        from tools.financial_tools import get_category_trends
        txns = [_make_tx(-100.0, "rent"), _make_tx(-50.0, "utilities")]
        result = await get_category_trends(_mock_db(txns), BUSINESS_ID, periods=3)
        assert "trends" in result
        assert isinstance(result["trends"], list)

    @pytest.mark.asyncio
    async def test_periods_key_matches_input(self):
        from tools.financial_tools import get_category_trends
        result = await get_category_trends(_mock_db([]), BUSINESS_ID, periods=4)
        assert result["periods"] == 4

    @pytest.mark.asyncio
    async def test_category_filter_respected(self):
        from tools.financial_tools import get_category_trends
        txns = [_make_tx(-100.0, "rent")]
        result = await get_category_trends(_mock_db(txns), BUSINESS_ID,
                                           category="rent", periods=2)
        assert result["category_filter"] == "rent"

    @pytest.mark.asyncio
    async def test_empty_data_returns_empty_trends(self):
        from tools.financial_tools import get_category_trends
        result = await get_category_trends(_mock_db([]), BUSINESS_ID, periods=3)
        # With no data, trends list may have entries but all totals should be 0
        totals = [r["total"] for r in result["trends"]]
        assert all(t == 0.0 for t in totals)

    @pytest.mark.asyncio
    async def test_period_labels_are_yyyy_mm(self):
        from tools.financial_tools import get_category_trends
        txns = [_make_tx(-100.0, "rent")]
        result = await get_category_trends(_mock_db(txns), BUSINESS_ID, periods=2)
        for entry in result["trends"]:
            import re
            assert re.match(r"\d{4}-\d{2}", entry["period"]), (
                f"Invalid period label: {entry['period']!r}"
            )
