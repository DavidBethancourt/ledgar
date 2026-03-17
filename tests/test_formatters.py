"""Tests for output formatters."""

import csv
import io
import json
import sys

import pytest

from ledgar.formatters import get_formatter
from ledgar.formatters.csv_fmt import (
    format_companies_csv,
    format_filings_csv,
    format_financials_csv,
)
from ledgar.formatters.json_fmt import (
    format_companies_json,
    format_filings_json,
    format_financials_json,
)


@pytest.fixture()
def company_rows():
    return [
        {"cik": 320193, "name": "Apple Inc.", "ticker": "AAPL"},
        {"cik": 789019, "name": "Microsoft Corporation", "ticker": "MSFT"},
    ]


@pytest.fixture()
def filing_rows():
    return [
        {
            "cik": 320193,
            "form_type": "10-K",
            "date_filed": "2023-11-03",
            "accession_number": "0000320193-23-000106",
            "file_path": "edgar/data/320193/0000320193-23-000106.txt",
        },
    ]


@pytest.fixture()
def financial_rows():
    return [
        {
            "period_end": "2023-09-30",
            "fiscal_year": 2023,
            "fiscal_period": "FY",
            "value": 383285000000,
            "unit": "USD",
            "metric": "Revenues",
            "form_type": "10-K",
            "accession_number": "0000320193-23-000106",
        },
    ]


class TestGetFormatter:
    def test_table_companies(self):
        fmt = get_formatter("table", "companies")
        assert callable(fmt)

    def test_json_financials(self):
        fmt = get_formatter("json", "financials")
        assert callable(fmt)

    def test_csv_filings(self):
        fmt = get_formatter("csv", "filings")
        assert callable(fmt)

    def test_invalid_format(self):
        with pytest.raises(KeyError):
            get_formatter("xml", "companies")

    def test_invalid_data_type(self):
        with pytest.raises(KeyError):
            get_formatter("table", "nonexistent")


class TestJsonFormatters:
    def test_companies_json(self, company_rows, capsys):
        format_companies_json(company_rows)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 2
        assert data[0]["ticker"] == "AAPL"

    def test_filings_json(self, filing_rows, capsys):
        format_filings_json(filing_rows)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["form_type"] == "10-K"

    def test_financials_json(self, financial_rows, capsys):
        format_financials_json(financial_rows)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data[0]["value"] == 383285000000


class TestCsvFormatters:
    def test_companies_csv(self, company_rows, capsys):
        format_companies_csv(company_rows)
        out = capsys.readouterr().out
        reader = csv.DictReader(io.StringIO(out))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["ticker"] == "AAPL"

    def test_filings_csv(self, filing_rows, capsys):
        format_filings_csv(filing_rows)
        out = capsys.readouterr().out
        reader = csv.DictReader(io.StringIO(out))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["form_type"] == "10-K"

    def test_financials_csv(self, financial_rows, capsys):
        format_financials_csv(financial_rows)
        out = capsys.readouterr().out
        reader = csv.DictReader(io.StringIO(out))
        rows = list(reader)
        assert rows[0]["period_end"] == "2023-09-30"
        assert rows[0]["context_fiscal_year"] == "2023"
        assert rows[0]["metric"] == "Revenues"

    def test_empty_rows(self, capsys):
        format_companies_csv([])
        out = capsys.readouterr().out
        assert out == ""
