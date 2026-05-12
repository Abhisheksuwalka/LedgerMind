"""
LangChain Tool Wrappers — Phase 4
====================================
Wraps the 6 financial tools from Phase 3 as LangChain @tool-decorated
async functions so the ReAct chat agent can call them via ToolNode.

Each tool docstring is written as a tool-use prompt — the LLM reads it
to decide WHEN to invoke the tool. Be precise and example-driven.

Design: tools are created at request-time via `build_chat_tools(db, business_id)`
so they close over the correct session and business context.
"""

import json
import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger("agents.chat_tools_lc")


def build_chat_tools(db, business_id: Optional[UUID]) -> list:
    """
    Build a list of LangChain tools bound to the given db session and business_id.
    Call this once per chat request, not at module load time.
    """
    from langchain_core.tools import tool

    # ── Tool 1: compute_pnl ───────────────────────────────────────────────────

    @tool
    async def compute_pnl(period: str = "last_30d") -> str:
        """Compute Profit & Loss (P&L) for a time period.
        Use when the user asks about revenue, expenses, profit, margin, or financial performance.
        Examples: 'What is my revenue?', 'How profitable am I?', 'What did I spend last month?'

        Args:
            period: Time period — one of: last_7d, last_30d, last_90d, this_month,
                    last_month, this_quarter, last_quarter, ytd, '2024-Q1', '2024-06'
        """
        from tools.financial_tools import compute_pnl as _impl
        result = await _impl(db, business_id, period)
        return json.dumps(result, default=str)

    # ── Tool 2: compute_runway ────────────────────────────────────────────────

    @tool
    async def compute_runway(additional_monthly_cost: float = 0.0) -> str:
        """Calculate months of cash runway at the current burn rate.
        Use when the user asks about sustainability, survival, hiring capacity,
        or 'can I afford X per month?'
        Examples: 'How long can I survive?', 'Can I afford a $3000/month hire?',
                  'What is my runway?', 'Am I running out of money?'

        Args:
            additional_monthly_cost: Extra monthly cost to model (e.g. 3000.0 for a new hire).
                                     Leave as 0 for current runway without changes.
        """
        from tools.financial_tools import compute_runway as _impl
        result = await _impl(db, business_id, additional_monthly_cost)
        return json.dumps(result, default=str)

    # ── Tool 3: query_transactions ────────────────────────────────────────────

    @tool
    async def query_transactions(
        period: str = "last_30d",
        category: Optional[str] = None,
        aggregate: Optional[str] = None,
        group_by: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """Query and explore transaction data with flexible filters and aggregations.
        Use when the user wants to see transactions, spending by category, or monthly totals.
        Examples: 'Show me my biggest expenses', 'What did I spend on software?',
                  'Break down spending by category', 'Monthly totals for this quarter'

        Args:
            period: Time period (last_30d, this_month, last_month, ytd, etc.)
            category: Filter by category name (e.g. 'rent', 'software', 'revenue')
            aggregate: One of 'sum', 'count', 'avg' — or None for raw transactions
            group_by: One of 'category', 'month' — groups aggregate results
            limit: Max number of raw transactions to return (default 20)
        """
        from tools.financial_tools import query_transactions as _impl
        result = await _impl(db, business_id, period, category, limit, aggregate, group_by)
        return json.dumps(result, default=str)

    # ── Tool 4: compare_periods ───────────────────────────────────────────────

    @tool
    async def compare_periods(
        period_a: str = "this_month",
        period_b: str = "last_month",
        metric: str = "revenue",
    ) -> str:
        """Compare a financial metric between two time periods.
        Use when the user asks about trends, changes, growth, or period comparisons.
        Examples: 'How does this month compare to last?', 'Is my revenue growing?',
                  'Revenue change this quarter vs last quarter'

        Args:
            period_a: The more recent period (e.g. 'this_month', 'this_quarter')
            period_b: The comparison baseline (e.g. 'last_month', 'last_quarter')
            metric: One of 'revenue', 'expenses', 'gross_profit', 'net_profit', 'margin_pct'
        """
        from tools.financial_tools import compare_periods as _impl
        result = await _impl(db, business_id, period_a, period_b, metric)
        return json.dumps(result, default=str)

    # ── Tool 5: find_anomalies ────────────────────────────────────────────────

    @tool
    async def find_anomalies(
        period: str = "last_30d",
        use_baselines: bool = True,
    ) -> str:
        """Find unusual or anomalous transactions that deviate from normal patterns.
        Use when the user asks about suspicious charges, outliers, unexpected expenses,
        or wants a financial health check.
        Examples: 'Any unusual transactions?', 'Do I have any anomalies?',
                  'Check for suspicious charges', 'What looks weird in my data?'

        Args:
            period: Time period to scan (last_30d, last_90d, this_quarter, etc.)
            use_baselines: Use learned category baselines for smarter detection (recommended)
        """
        from tools.financial_tools import find_anomalies as _impl
        result = await _impl(db, business_id, period, use_baselines)
        return json.dumps(result, default=str)

    # ── Tool 6: get_category_trends ───────────────────────────────────────────

    @tool
    async def get_category_trends(
        category: Optional[str] = None,
        periods: int = 6,
    ) -> str:
        """Get spending trends per category over multiple months.
        Use when the user asks about trends, growth patterns, or wants to see
        how spending in a category has changed over time.
        Examples: 'Show me spending trends', 'Is my rent increasing?',
                  'How has marketing spend changed?', 'Category breakdown over 6 months'

        Args:
            category: Specific category to focus on (e.g. 'rent', 'software'). None = all categories.
            periods: Number of months to look back (default 6)
        """
        from tools.financial_tools import get_category_trends as _impl
        result = await _impl(db, business_id, category, periods)
        return json.dumps(result, default=str)

    return [
        compute_pnl,
        compute_runway,
        query_transactions,
        compare_periods,
        find_anomalies,
        get_category_trends,
    ]
