"""CSV output formatter."""

import csv
import sys


def format_companies_csv(rows: list[dict]) -> None:
    """Output companies as CSV to stdout."""
    if not rows:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=["cik", "ticker", "name"])
    writer.writeheader()
    writer.writerows(rows)


def format_financials_csv(rows: list[dict]) -> None:
    """Output financial data as CSV to stdout."""
    if not rows:
        return
    fields = [
        "period_end", "context_fiscal_year", "fiscal_period", "value", "unit",
        "metric", "form_type", "accession_number",
    ]
    normalized_rows = [
        {
            "period_end": row.get("period_end", ""),
            "context_fiscal_year": row.get("fiscal_year", ""),
            "fiscal_period": row.get("fiscal_period", ""),
            "value": row.get("value", ""),
            "unit": row.get("unit", ""),
            "metric": row.get("metric", ""),
            "form_type": row.get("form_type", ""),
            "accession_number": row.get("accession_number", ""),
        }
        for row in rows
    ]
    writer = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(normalized_rows)


def format_filings_csv(rows: list[dict]) -> None:
    """Output filings as CSV to stdout."""
    if not rows:
        return
    fields = ["cik", "form_type", "date_filed", "accession_number", "file_path"]
    writer = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
