"""JSON output formatter."""

import json
import sys


def format_companies_json(rows: list[dict]) -> None:
    """Output companies as JSON to stdout."""
    json.dump(rows, sys.stdout, indent=2)
    sys.stdout.write("\n")


def format_financials_json(rows: list[dict]) -> None:
    """Output financial data as JSON to stdout."""
    json.dump(rows, sys.stdout, indent=2)
    sys.stdout.write("\n")


def format_filings_json(rows: list[dict]) -> None:
    """Output filings as JSON to stdout."""
    json.dump(rows, sys.stdout, indent=2)
    sys.stdout.write("\n")
