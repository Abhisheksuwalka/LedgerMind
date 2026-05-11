"""
F3 — Unit tests for Data Ingestion's parse_csv() function.
Pure Python — no DB, no LLM, no network.

Run:
    cd backend && python -m pytest tests/test_ingestion.py -v
"""

import io
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_ingestion import parse_csv, _infer_category


VALID_CSV = b"""date,description,amount,category
2024-01-15,Monthly SaaS Revenue,12000,revenue
2024-01-15,AWS Infrastructure,-1200,expense
2024-01-16,Staff Salaries,-8500,expense
2024-01-17,Consulting Invoice,3000,revenue
"""

VALID_CSV_NO_CATEGORY = b"""date,description,amount
2024-01-15,Monthly SaaS Revenue,12000
2024-01-15,AWS Infrastructure,-1200
2024-01-16,Staff Salaries,-8500
2024-01-17,Payment,-2000
"""


class TestParseCsv:

    def test_valid_csv_parses_correctly(self):
        """Valid CSV with all columns should parse cleanly."""
        df = parse_csv(VALID_CSV)

        assert len(df) == 4
        assert list(df.columns[:3]) == ["date", "description", "amount"]
        # amounts correct
        assert df["amount"].iloc[0] == 12000.0
        assert df["amount"].iloc[1] == -1200.0
        # categories preserved
        assert df["category"].iloc[0] == "revenue"
        assert df["category"].iloc[2] == "expense"

    def test_missing_required_column_raises(self):
        """CSV without the 'amount' column should raise ValueError."""
        bad_csv = b"date,description\n2024-01-01,Test\n"

        with pytest.raises(ValueError, match="missing required columns"):
            parse_csv(bad_csv)

    def test_category_inferred_when_absent(self):
        """CSV without a category column — categories inferred from description."""
        df = parse_csv(VALID_CSV_NO_CATEGORY)

        assert "category" in df.columns
        # "Monthly SaaS Revenue" → no keyword match → "other"
        # "AWS Infrastructure" → no keyword match → "other"
        # "Payment" → matches keyword "payment" → "expense"
        assert df["category"].iloc[3] == "expense"

    def test_columns_normalised_lowercase(self):
        """Columns with spaces and mixed case should be normalised."""
        csv_with_spaces = b"Date , Description , Amount\n2024-01-01,Test,100\n"
        df = parse_csv(csv_with_spaces)

        assert "date" in df.columns
        assert "description" in df.columns
        assert "amount" in df.columns

    def test_amounts_coerced_to_float(self):
        """Amounts should be float, not string."""
        df = parse_csv(VALID_CSV)

        assert df["amount"].dtype.name == "float64"

    def test_default_currency_usd(self):
        """CSV without currency column — should default to USD."""
        df = parse_csv(VALID_CSV)

        assert "currency" in df.columns
        assert all(df["currency"] == "USD")


class TestInferCategory:

    def test_payment_keyword(self):
        assert _infer_category("Credit Card Payment") == "expense"

    def test_salary_keyword(self):
        assert _infer_category("Monthly Salary Disbursement") == "revenue"

    def test_rent_keyword(self):
        assert _infer_category("Office Rent Q1") == "expense"

    def test_refund_keyword(self):
        assert _infer_category("Customer Refund Processed") == "revenue"

    def test_no_keyword_match(self):
        assert _infer_category("Miscellaneous item 42") == "other"

    def test_case_insensitive(self):
        assert _infer_category("MARKETING Campaign") == "expense"
