"""Parse EDGAR JSON responses into database-ready structures."""

import logging
import re

log = logging.getLogger(__name__)

# --- Company Tickers ---

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def parse_company_tickers(data: dict) -> list[tuple[int, str, str]]:
    """Parse company_tickers.json into (cik, ticker, name) tuples."""
    results = []
    for entry in data.values():
        cik = int(entry["cik_str"])
        ticker = entry.get("ticker", "")
        name = entry.get("title", "")
        results.append((cik, ticker, name))
    return results


# --- Company Facts (XBRL) ---

COMPANYFACTS_SINGLE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
COMPANYFACTS_BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"


def parse_company_facts(cik: int, data: dict) -> list[dict]:
    """Parse a single company's XBRL facts JSON into financial_facts rows."""
    rows = []
    facts = data.get("facts", {})
    for taxonomy, metrics in facts.items():
        for metric_name, metric_data in metrics.items():
            label = metric_data.get("label", "")
            units = metric_data.get("units", {})
            for unit_name, data_points in units.items():
                for dp in data_points:
                    rows.append({
                        "cik": cik,
                        "taxonomy": taxonomy,
                        "metric": metric_name,
                        "label": label,
                        "period_start": dp.get("start"),
                        "period_end": dp.get("end"),
                        "value": dp.get("val"),
                        "unit": unit_name,
                        "form_type": dp.get("form"),
                        "accession_number": dp.get("accn"),
                        "fiscal_year": dp.get("fy"),
                        "fiscal_period": dp.get("fp"),
                    })
    return rows


# --- Full Index (master.idx) ---

FULL_INDEX_URL = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"

_ACCESSION_RE = re.compile(r"\d{10}-\d{2}-\d{6}")


def parse_master_index(text: str) -> list[dict]:
    """Parse a master.idx file into filings rows."""
    rows = []
    in_data = False
    for line in text.splitlines():
        if line.startswith("---"):
            in_data = True
            continue
        if not in_data:
            continue
        parts = line.split("|")
        if len(parts) != 5:
            continue
        cik_str, _company_name, form_type, date_filed, filename = parts
        accn_match = _ACCESSION_RE.search(filename)
        accession_number = accn_match.group(0) if accn_match else ""
        rows.append({
            "cik": int(cik_str.strip()),
            "form_type": form_type.strip(),
            "date_filed": date_filed.strip(),
            "accession_number": accession_number,
            "file_path": filename.strip(),
        })
    return rows


# --- XBRL Metric Aliases ---

METRIC_ALIASES: dict[str, list[str]] = {
    # Income Statement
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    "cost-of-revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "gross-profit": ["GrossProfit"],
    "operating-income": ["OperatingIncomeLoss"],
    "net-income": ["NetIncomeLoss"],
    "eps-basic": ["EarningsPerShareBasic"],
    "eps-diluted": ["EarningsPerShareDiluted"],
    # Balance Sheet
    "total-assets": ["Assets"],
    "total-liabilities": ["Liabilities"],
    "stockholders-equity": ["StockholdersEquity"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "current-assets": ["AssetsCurrent"],
    "current-liabilities": ["LiabilitiesCurrent"],
    # Cash Flow Statement
    "operating-cash-flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "investing-cash-flow": ["NetCashProvidedByUsedInInvestingActivities"],
    "financing-cash-flow": ["NetCashProvidedByUsedInFinancingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}


def resolve_metric(friendly_name: str) -> list[str]:
    """Return XBRL tags for a friendly metric name."""
    tags = METRIC_ALIASES.get(friendly_name)
    if not tags:
        raise ValueError(
            f"Unknown metric '{friendly_name}'. "
            f"Available: {', '.join(sorted(METRIC_ALIASES))}"
        )
    return tags


def list_metrics() -> list[str]:
    """Return all available friendly metric names."""
    return sorted(METRIC_ALIASES.keys())
