"""Tests for the DataStore class."""

import pytest


class TestMetadata:
    def test_set_and_get(self, tmp_db):
        tmp_db.set_metadata("test-key", "test-value")
        assert tmp_db.get_metadata("test-key") == "test-value"

    def test_get_missing_key(self, tmp_db):
        assert tmp_db.get_metadata("nonexistent") is None

    def test_set_metadata_now(self, tmp_db):
        tmp_db.set_metadata_now("timestamp-key")
        val = tmp_db.get_metadata("timestamp-key")
        assert val is not None
        assert "T" in val  # ISO format

    def test_overwrite(self, tmp_db):
        tmp_db.set_metadata("key", "v1")
        tmp_db.set_metadata("key", "v2")
        assert tmp_db.get_metadata("key") == "v2"


class TestCompanies:
    def test_insert_and_search_by_name(self, tmp_db, sample_companies):
        count = tmp_db.insert_companies(sample_companies)
        assert count == 5
        results = tmp_db.search_companies_by_name("Apple")
        assert len(results) == 1
        assert results[0]["ticker"] == "AAPL"

    def test_search_by_ticker(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        result = tmp_db.search_company_by_ticker("MSFT")
        assert result is not None
        assert result["name"] == "Microsoft Corporation"

    def test_search_by_ticker_case_insensitive(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        result = tmp_db.search_company_by_ticker("msft")
        assert result is not None

    def test_search_by_ticker_not_found(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        assert tmp_db.search_company_by_ticker("ZZZZ") is None

    def test_get_cik_for_ticker(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        assert tmp_db.get_cik_for_ticker("AAPL") == 320193

    def test_get_cik_for_ticker_not_found(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        assert tmp_db.get_cik_for_ticker("ZZZZ") is None

    def test_fts_prefix_search(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        results = tmp_db.search_companies_by_name("Micro")
        assert len(results) == 1
        assert results[0]["ticker"] == "MSFT"

    def test_insert_replaces_on_conflict(self, tmp_db):
        tmp_db.insert_companies([(1, "Old Name", "OLD")])
        tmp_db.insert_companies([(1, "New Name", "NEW")])
        result = tmp_db.search_company_by_ticker("NEW")
        assert result is not None
        assert result["name"] == "New Name"


class TestFinancialFacts:
    def test_insert_and_search(self, tmp_db, sample_companies, sample_financial_facts):
        tmp_db.insert_companies(sample_companies)
        count = tmp_db.insert_financial_facts(sample_financial_facts)
        assert count == 4

        results = tmp_db.search_financials(320193, ["Revenues"])
        assert len(results) >= 2

    def test_period_filter_annual(self, tmp_db, sample_companies, sample_financial_facts):
        tmp_db.insert_companies(sample_companies)
        tmp_db.insert_financial_facts(sample_financial_facts)

        results = tmp_db.search_financials(320193, ["Revenues"], period="annual")
        assert all(r["fiscal_period"] == "FY" for r in results)

    def test_period_filter_quarterly(self, tmp_db, sample_companies, sample_financial_facts):
        tmp_db.insert_companies(sample_companies)
        tmp_db.insert_financial_facts(sample_financial_facts)

        results = tmp_db.search_financials(320193, ["Revenues"], period="quarterly")
        assert all(r["fiscal_period"] in ("Q1", "Q2", "Q3", "Q4") for r in results)

    def test_empty_results(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        results = tmp_db.search_financials(320193, ["NonexistentMetric"])
        assert results == []

    def test_insert_empty(self, tmp_db):
        assert tmp_db.insert_financial_facts([]) == 0

    def test_dedup_ignores_duplicate(self, tmp_db, sample_companies, sample_financial_facts):
        tmp_db.insert_companies(sample_companies)
        tmp_db.insert_financial_facts(sample_financial_facts)
        # Insert same facts again — should not error due to INSERT OR IGNORE
        tmp_db.insert_financial_facts(sample_financial_facts)


class TestFilings:
    def test_insert_and_search(self, tmp_db, sample_companies, sample_filings):
        tmp_db.insert_companies(sample_companies)
        count = tmp_db.insert_filings(sample_filings)
        assert count == 4

        results = tmp_db.search_filings(320193)
        assert len(results) == 3

    def test_filter_by_form_type(self, tmp_db, sample_companies, sample_filings):
        tmp_db.insert_companies(sample_companies)
        tmp_db.insert_filings(sample_filings)

        results = tmp_db.search_filings(320193, form_type="10-K")
        assert len(results) == 1
        assert results[0]["form_type"] == "10-K"

    def test_filter_by_date_range(self, tmp_db, sample_companies, sample_filings):
        tmp_db.insert_companies(sample_companies)
        tmp_db.insert_filings(sample_filings)

        results = tmp_db.search_filings(
            320193, start_date="2024-01-01", end_date="2024-12-31"
        )
        assert len(results) == 2
        assert all(r["date_filed"] >= "2024-01-01" for r in results)

    def test_empty_results(self, tmp_db, sample_companies):
        tmp_db.insert_companies(sample_companies)
        results = tmp_db.search_filings(999999)
        assert results == []

    def test_insert_empty(self, tmp_db):
        assert tmp_db.insert_filings([]) == 0

    def test_ordered_by_date_desc(self, tmp_db, sample_companies, sample_filings):
        tmp_db.insert_companies(sample_companies)
        tmp_db.insert_filings(sample_filings)

        results = tmp_db.search_filings(320193)
        dates = [r["date_filed"] for r in results]
        assert dates == sorted(dates, reverse=True)
