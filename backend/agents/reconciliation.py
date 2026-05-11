"""
Agent 6 — Reconciliation Agent
Period-over-period category variance analysis.
Compares current run's category averages to the previous run stored in DB.
Flags categories where spend deviated > 20% from the prior period.
"""

import logging
from collections import defaultdict
from typing import Optional

from tools.llm_router import run_agent
from tools.json_utils import extract_json_object

logger = logging.getLogger("agent.reconciliation")

SYSTEM_PROMPT = """You are an expert reconciliation accountant AI specialising in SaaS financial operations.

You have been given a period-over-period category variance analysis comparing this period's spending
against the previous period's averages.

Your task:
1. Identify which category variances are normal (seasonal, growth) vs. concerning (overspend, fraud).
2. Suggest the most likely root causes for the largest deviations.
3. Provide a prioritised action plan for the finance team.

Respond with a JSON object:
{
  "root_cause_analysis": "2-3 sentence summary of key variances and likely causes",
  "action_plan": ["step1", "step2", ...],
  "risk_level": "low|medium|high",
  "estimated_resolution_hours": 0
}"""


def _compute_period_variance(transactions: list[dict]) -> dict:
    """
    Period-over-period variance:
    - Split transactions into two halves by date (older = 'previous', newer = 'current')
    - Compute per-category totals in each half
    - Flag categories with >20% variance between periods
    """
    if not transactions:
        return {
            "total_transactions": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "discrepancy_count": 0,
            "match_rate_pct": 0.0,
            "top_discrepancies": [],
            "unmatched_sample": [],
            "period_variance": [],
        }

    # Sort by date and split into two halves
    sorted_txns = sorted(transactions, key=lambda x: x.get("date", ""))
    mid = len(sorted_txns) // 2
    previous = sorted_txns[:mid]
    current = sorted_txns[mid:]

    def cat_totals(txns: list[dict]) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for tx in txns:
            totals[tx.get("category", "other")] += float(tx.get("amount", 0))
        return dict(totals)

    prev_totals = cat_totals(previous)
    curr_totals = cat_totals(current)

    all_cats = set(prev_totals) | set(curr_totals)
    variances = []
    discrepancies = []

    for cat in sorted(all_cats):
        prev_val = prev_totals.get(cat, 0.0)
        curr_val = curr_totals.get(cat, 0.0)

        if prev_val == 0:
            pct_change = 100.0 if curr_val != 0 else 0.0
        else:
            pct_change = ((curr_val - prev_val) / abs(prev_val)) * 100

        entry = {
            "category": cat,
            "previous_period": round(prev_val, 2),
            "current_period": round(curr_val, 2),
            "pct_change": round(pct_change, 1),
            "flag": abs(pct_change) > 20,
        }
        variances.append(entry)
        if abs(pct_change) > 20:
            discrepancies.append(entry)

    flagged_count = len(discrepancies)
    total = len(transactions)

    # "Matched" = categories with <= 20% variance (stable spend)
    matched_count = len(all_cats) - flagged_count

    return {
        "total_transactions": total,
        "matched_count": matched_count,
        "unmatched_count": 0,
        "discrepancy_count": flagged_count,
        "match_rate_pct": round(matched_count / len(all_cats) * 100, 1) if all_cats else 0.0,
        "top_discrepancies": discrepancies[:5],
        "unmatched_sample": [],
        "period_variance": variances,
    }


async def reconcile(ingestion_result: dict, run_id: Optional[str] = None) -> dict:
    logger.info("[ReconciliationAgent] Running for run_id=%s", run_id)

    transactions = ingestion_result.get("transactions", [])
    computed = _compute_period_variance(transactions)

    context = {
        "run_id": run_id,
        "reconciliation_summary": computed,
        "period_variance": computed.get("period_variance", []),
    }

    llm_result = await run_agent(
        system_prompt=SYSTEM_PROMPT,
        context=context,
        max_tokens=800,
    )

    raw = llm_result["text"]
    parsed = extract_json_object(raw) or {}

    logger.info(
        "[ReconciliationAgent] match_rate=%.1f%%, discrepancies=%d  [provider=%s, %dms]",
        computed["match_rate_pct"],
        computed["discrepancy_count"],
        llm_result.get("provider", "?"),
        llm_result.get("duration_ms", 0),
    )

    return {
        **computed,
        "root_cause_analysis": parsed.get("root_cause_analysis", ""),
        "action_plan": parsed.get("action_plan", []),
        "risk_level": parsed.get("risk_level", "medium"),
        "tokens_used": llm_result["tokens_used"],
        "llm_provider": llm_result.get("provider"),
    }
