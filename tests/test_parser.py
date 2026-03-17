"""Tests for EDGAR parser functions."""

from ledgar.edgar.parser import (
    METRIC_ALIASES,
    list_metrics,
    parse_company_facts,
    parse_company_tickers,
    parse_master_index,
    resolve_metric,
)


class TestParseCompanyTickers:
    def test_basic_parsing(self, sample_company_tickers_json):
        rows = parse_company_tickers(sample_company_tickers_json)
        assert len(rows) == 3
        # Each tuple is (cik, name, ticker)
        ciks = [r[0] for r in rows]
        assert 320193 in ciks
        assert 789019 in ciks

    def test_tuple_format(self, sample_company_tickers_json):
        rows = parse_company_tickers(sample_company_tickers_json)
        apple = [r for r in rows if r[0] == 320193][0]
        assert apple == (320193, "Apple Inc.", "AAPL")

    def test_empty_input(self):
        assert parse_company_tickers({}) == []


class TestParseCompanyFacts:
    def test_basic_parsing(self):
        data = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "label": "Revenues",
                        "units": {
                            "USD": [
                                {
                                    "start": "2022-01-01",
                                    "end": "2022-12-31",
                                    "val": 100000,
                                    "form": "10-K",
                                    "accn": "0001234567-23-000001",
                                    "fy": 2022,
                                    "fp": "FY",
                                }
                            ]
                        },
                    }
                }
            }
        }
        rows = parse_company_facts(123, data)
        assert len(rows) == 1
        assert rows[0]["cik"] == 123
        assert rows[0]["metric"] == "Revenues"
        assert rows[0]["value"] == 100000
        assert rows[0]["taxonomy"] == "us-gaap"
        assert rows[0]["fiscal_year"] == 2022

    def test_empty_facts(self):
        assert parse_company_facts(123, {"facts": {}}) == []
        assert parse_company_facts(123, {}) == []


class TestParseMasterIndex:
    def test_basic_parsing(self, sample_master_idx):
        rows = parse_master_index(sample_master_idx)
        assert len(rows) == 3
        assert rows[0]["cik"] == 320193
        assert rows[0]["form_type"] == "10-K"
        assert rows[0]["date_filed"] == "2023-11-03"

    def test_accession_number_extraction(self, sample_master_idx):
        rows = parse_master_index(sample_master_idx)
        assert rows[0]["accession_number"] == "0000320193-23-000106"

    def test_empty_input(self):
        assert parse_master_index("") == []

    def test_header_only(self):
        text = "CIK|Company Name|Form Type|Date Filed|Filename\n---\n"
        assert parse_master_index(text) == []


class TestResolveMetric:
    def test_known_metric(self):
        tags = resolve_metric("revenue")
        assert "Revenues" in tags
        assert isinstance(tags, list)

    def test_unknown_metric(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown metric"):
            resolve_metric("nonexistent-metric")

    def test_all_aliases_resolve(self):
        for name in METRIC_ALIASES:
            tags = resolve_metric(name)
            assert len(tags) > 0


class TestListMetrics:
    def test_returns_sorted(self):
        metrics = list_metrics()
        assert metrics == sorted(metrics)
        assert len(metrics) == len(METRIC_ALIASES)
