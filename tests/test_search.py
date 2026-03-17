"""Tests for search CLI commands."""

import json

from click.testing import CliRunner

from ledgar.db.store import DataStore
from ledgar.ledgar import cli


def _setup_db(tmp_path, companies=None, filings=None, facts=None):
    """Create a test database in the expected location."""
    db_path = tmp_path / "ledgar.db"
    store = DataStore(str(db_path))
    if companies:
        store.insert_companies(companies)
    if filings:
        store.insert_filings(filings)
    if facts:
        store.insert_financial_facts(facts)
    store.close()


class TestSearchCompany:
    def test_search_by_name(self, tmp_path, sample_companies):
        _setup_db(tmp_path, companies=sample_companies)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--data-dir", str(tmp_path), "search", "company", "--name", "Apple"],
        )
        assert result.exit_code == 0
        assert "Apple" in result.output

    def test_search_by_ticker(self, tmp_path, sample_companies):
        _setup_db(tmp_path, companies=sample_companies)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--data-dir", str(tmp_path), "search", "company", "--ticker", "MSFT"],
        )
        assert result.exit_code == 0
        assert "Microsoft" in result.output

    def test_search_json_output(self, tmp_path, sample_companies):
        _setup_db(tmp_path, companies=sample_companies)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--data-dir", str(tmp_path),
                "search", "--output", "json",
                "company", "--ticker", "AAPL",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["ticker"] == "AAPL"

    def test_no_options_error(self, tmp_path, sample_companies):
        _setup_db(tmp_path, companies=sample_companies)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--data-dir", str(tmp_path), "search", "company"],
        )
        assert result.exit_code != 0


class TestSearchFiling:
    def test_search_by_cik(self, tmp_path, sample_companies, sample_filings):
        _setup_db(tmp_path, companies=sample_companies, filings=sample_filings)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--data-dir", str(tmp_path), "search", "filing", "--cik", "320193"],
        )
        assert result.exit_code == 0
        assert "10-K" in result.output

    def test_search_by_ticker(self, tmp_path, sample_companies, sample_filings):
        _setup_db(tmp_path, companies=sample_companies, filings=sample_filings)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--data-dir", str(tmp_path), "search", "filing", "--ticker", "AAPL"],
        )
        assert result.exit_code == 0
        assert "10-K" in result.output

    def test_filter_by_form_type(self, tmp_path, sample_companies, sample_filings):
        _setup_db(tmp_path, companies=sample_companies, filings=sample_filings)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--data-dir", str(tmp_path),
                "search", "filing",
                "--ticker", "AAPL", "--form-type", "8-K",
            ],
        )
        assert result.exit_code == 0
        assert "8-K" in result.output
        # Should not contain 10-K
        assert "10-K" not in result.output


class TestSearchFinancials:
    def test_search_by_ticker(
        self, tmp_path, sample_companies, sample_financial_facts
    ):
        _setup_db(tmp_path, companies=sample_companies, facts=sample_financial_facts)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--data-dir", str(tmp_path),
                "search", "financials",
                "--ticker", "AAPL", "--metric", "revenue",
            ],
        )
        assert result.exit_code == 0

    def test_invalid_metric(self, tmp_path, sample_companies):
        _setup_db(tmp_path, companies=sample_companies)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--data-dir", str(tmp_path),
                "search", "financials",
                "--ticker", "AAPL", "--metric", "fake-metric",
            ],
        )
        assert result.exit_code != 0
        assert "Unknown metric" in result.output
