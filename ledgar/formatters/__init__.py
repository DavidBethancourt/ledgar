"""Output formatters."""

from typing import Callable

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
from ledgar.formatters.table import (
    format_companies_table,
    format_filings_table,
    format_financials_table,
)

_FORMATTERS: dict[str, dict[str, Callable]] = {
    "table": {
        "companies": format_companies_table,
        "financials": format_financials_table,
        "filings": format_filings_table,
    },
    "json": {
        "companies": format_companies_json,
        "financials": format_financials_json,
        "filings": format_filings_json,
    },
    "csv": {
        "companies": format_companies_csv,
        "financials": format_financials_csv,
        "filings": format_filings_csv,
    },
}


def get_formatter(output_format: str, data_type: str) -> Callable:
    """Return the appropriate formatter function."""
    return _FORMATTERS[output_format][data_type]
