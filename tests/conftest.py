"""Shared test fixtures."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from ledgar.db.schema import create_tables
from ledgar.db.store import DataStore


@pytest.fixture()
def tmp_db(tmp_path):
    """Return a DataStore backed by a temporary SQLite database."""
    db_path = tmp_path / "test.db"
    store = DataStore(str(db_path))
    yield store
    store.close()


@pytest.fixture()
def sample_companies():
    """Sample company tuples (cik, name, ticker)."""
    return [
        (320193, "Apple Inc.", "AAPL"),
        (789019, "Microsoft Corporation", "MSFT"),
        (1018724, "Amazon.com Inc.", "AMZN"),
        (1652044, "Alphabet Inc.", "GOOGL"),
        (1045810, "NVIDIA Corporation", "NVDA"),
    ]


@pytest.fixture()
def sample_financial_facts():
    """Sample financial fact dicts."""
    return [
        {
            "cik": 320193,
            "taxonomy": "us-gaap",
            "metric": "Revenues",
            "label": "Revenues",
            "period_start": "2022-09-25",
            "period_end": "2023-09-30",
            "value": 383285000000,
            "unit": "USD",
            "form_type": "10-K",
            "accession_number": "0000320193-23-000106",
            "fiscal_year": 2023,
            "fiscal_period": "FY",
        },
        {
            "cik": 320193,
            "taxonomy": "us-gaap",
            "metric": "Revenues",
            "label": "Revenues",
            "period_start": "2021-09-26",
            "period_end": "2022-09-24",
            "value": 394328000000,
            "unit": "USD",
            "form_type": "10-K",
            "accession_number": "0000320193-22-000108",
            "fiscal_year": 2022,
            "fiscal_period": "FY",
        },
        {
            "cik": 320193,
            "taxonomy": "us-gaap",
            "metric": "NetIncomeLoss",
            "label": "Net Income",
            "period_start": "2022-09-25",
            "period_end": "2023-09-30",
            "value": 96995000000,
            "unit": "USD",
            "form_type": "10-K",
            "accession_number": "0000320193-23-000106",
            "fiscal_year": 2023,
            "fiscal_period": "FY",
        },
        {
            "cik": 320193,
            "taxonomy": "us-gaap",
            "metric": "Revenues",
            "label": "Revenues",
            "period_start": "2023-07-02",
            "period_end": "2023-09-30",
            "value": 89498000000,
            "unit": "USD",
            "form_type": "10-Q",
            "accession_number": "0000320193-23-000077",
            "fiscal_year": 2023,
            "fiscal_period": "Q4",
        },
    ]


@pytest.fixture()
def sample_filings():
    """Sample filing dicts."""
    return [
        {
            "cik": 320193,
            "form_type": "10-K",
            "date_filed": "2023-11-03",
            "accession_number": "0000320193-23-000106",
            "file_path": "edgar/data/320193/0000320193-23-000106.txt",
        },
        {
            "cik": 320193,
            "form_type": "10-Q",
            "date_filed": "2024-02-02",
            "accession_number": "0000320193-24-000006",
            "file_path": "edgar/data/320193/0000320193-24-000006.txt",
        },
        {
            "cik": 320193,
            "form_type": "8-K",
            "date_filed": "2024-02-01",
            "accession_number": "0000320193-24-000005",
            "file_path": "edgar/data/320193/0000320193-24-000005.txt",
        },
        {
            "cik": 789019,
            "form_type": "10-K",
            "date_filed": "2023-07-27",
            "accession_number": "0000789019-23-000023",
            "file_path": "edgar/data/789019/0000789019-23-000023.txt",
        },
    ]


@pytest.fixture()
def sample_company_tickers_json():
    """Sample company_tickers.json response body."""
    return {
        "0": {"cik_str": "320193", "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": "789019", "ticker": "MSFT", "title": "Microsoft Corporation"},
        "2": {"cik_str": "1018724", "ticker": "AMZN", "title": "Amazon.com Inc."},
    }


@pytest.fixture()
def sample_master_idx():
    """Sample master.idx content."""
    return (
        "CIK|Company Name|Form Type|Date Filed|Filename\n"
        "-----------------------------------------------------------\n"
        "320193|Apple Inc.|10-K|2023-11-03|edgar/data/320193/0000320193-23-000106.txt\n"
        "320193|Apple Inc.|8-K|2024-02-01|edgar/data/320193/0000320193-24-000005.txt\n"
        "789019|MICROSOFT CORP|10-K|2023-07-27|edgar/data/789019/0000789019-23-000023.txt\n"
    )
