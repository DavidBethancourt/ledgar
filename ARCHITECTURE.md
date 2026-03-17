# Architecture

> **Purpose of this file:** Technical deep dive — EDGAR data sources, JSON response
> structures, XBRL metric mapping, database schema, data flow, error handling, and
> data refresh strategy. This is the "how it works under the hood" document.
>
> **Not for:** Build sequencing or project layout (see [AGENTS.md](AGENTS.md)),
> end-user usage (see [README.md](README.md)), or coding standards
> (see [CONTRIBUTING.md](CONTRIBUTING.md)).

---

## Data Flow

```
┌─────────────────┐       ┌──────────────┐       ┌────────────┐
│  SEC EDGAR APIs │──HTTP──▶  edgar/      │──parse─▶  db/       │
│  (one-time DL)  │       │  client.py   │       │  store.py  │
│                 │       │  bulk.py     │       │  schema.py │
│                 │       │  parser.py   │       │            │
└─────────────────┘       └──────────────┘       └─────┬──────┘
                                                       │
                                                       │ SQLite
                                                       ▼
┌─────────────────┐       ┌──────────────┐       ┌────────────┐
│  Terminal        │◀─────│  formatters/ │◀──rows─│  ledgar.db │
│  (stdout)       │       │  table.py    │       │            │
│                 │       │  json_fmt.py │       │            │
│                 │       │  csv_fmt.py  │       │            │
└─────────────────┘       └──────────────┘       └────────────┘
```

**Download path:** SEC EDGAR → `edgar/client.py` (HTTP + rate limiting) → `edgar/parser.py` (JSON parsing) → `db/store.py` (SQLite insert)

**Query path:** CLI command → `db/store.py` (SQL query) → `formatters/` (table/json/csv) → stdout

---

## EDGAR Data Sources

### Primary Sources (Financial Statements)

| Source | URL | Content |
|---|---|---|
| Bulk XBRL Company Facts | <https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip> | All structured financial data for every company (~1.5 GB ZIP). One JSON file per CIK containing all reported XBRL metrics across all filings. |
| Single Company Facts | `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` | Structured financial facts for a single company. Useful for incremental updates. |
| Company Tickers JSON | <https://www.sec.gov/files/company_tickers.json> | CIK ↔ ticker ↔ company name mapping. |
| Full-Text Filing Index | `https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{q}/` | Master index of all filings by year/quarter. Contains form type, CIK, date filed, accession number, and file path. |
| XBRL Frames | `https://data.sec.gov/api/xbrl/frames/us-gaap/{metric}/USD/CY{year}.json` | Cross-company comparison for a single metric in a single period. |

### EDGAR Documentation

- [EDGAR Developer Resources & APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) — official API list and documentation
- [Accessing EDGAR Data (Bulk Downloads & Rate Limits)](https://www.sec.gov/os/accessing-edgar-data) — bulk download paths, `User-Agent` requirement, 10 req/sec limit
- [EDGAR Full-Text Search System](https://efts.sec.gov/LATEST/search-index?q=%22full-text%22&dateRange=custom&startdt=2021-01-01&enddt=2024-12-31) — EFTS search interface
- [SEC EDGAR Company Search](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany) — web-based company/filing lookup

### Future Data Sources (Not In Scope Yet)

| Source | Content |
|---|---|
| Insider Transactions (Forms 3, 4, 5) | Officer/director stock purchases and sales |
| Institutional Holdings (Form 13F) | Quarterly holdings of institutional investment managers |
| Proxy Statements (DEF 14A) | Executive compensation, board composition |
| 8-K Current Reports | Material events (earnings, M&A, leadership changes) |

---

## CIK Formatting

SEC API URLs require CIKs **zero-padded to 10 digits**:

```
CIK (integer):   320193
API URL format:   CIK0000320193.json
Full URL:         https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json
```

The `edgar/client.py` module must handle this normalization. Store CIKs as integers in SQLite; format to zero-padded strings only when constructing URLs.

---

## EDGAR JSON Response Structures

### Company Tickers (`company_tickers.json`)

```json
{
  "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
  "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
  "2": {"cik_str": 1652044, "ticker": "GOOGL", "title": "Alphabet Inc."}
}
```

Top-level keys are string indices. Each entry has `cik_str` (integer), `ticker`, and `title`.

### Company Facts (`companyfacts/CIK{cik}.json`)

This is the core data structure. Each file contains all XBRL-reported metrics for one company.

```json
{
  "cik": 320193,
  "entityName": "Apple Inc.",
  "facts": {
    "dei": {
      "EntityCommonStockSharesOutstanding": {
        "label": "Entity Common Stock, Shares Outstanding",
        "description": "...",
        "units": {
          "shares": [
            {
              "end": "2023-09-30",
              "val": 15550061000,
              "accn": "0000320193-23-000106",
              "fy": 2023,
              "fp": "FY",
              "form": "10-K",
              "filed": "2023-11-03"
            }
          ]
        }
      }
    },
    "us-gaap": {
      "Revenues": {
        "label": "Revenues",
        "description": "Amount of revenue recognized...",
        "units": {
          "USD": [
            {
              "start": "2022-10-01",
              "end": "2023-09-30",
              "val": 383285000000,
              "accn": "0000320193-23-000106",
              "fy": 2023,
              "fp": "FY",
              "form": "10-K",
              "filed": "2023-11-03"
            },
            {
              "start": "2023-07-02",
              "end": "2023-09-30",
              "val": 89498000000,
              "accn": "0000320193-23-000106",
              "fy": 2023,
              "fp": "Q4",
              "form": "10-K",
              "filed": "2023-11-03"
            }
          ]
        }
      },
      "NetIncomeLoss": {
        "label": "Net Income (Loss)",
        "description": "...",
        "units": {
          "USD": [
            {
              "start": "2022-10-01",
              "end": "2023-09-30",
              "val": 96995000000,
              "accn": "0000320193-23-000106",
              "fy": 2023,
              "fp": "FY",
              "form": "10-K",
              "filed": "2023-11-03"
            }
          ]
        }
      }
    }
  }
}
```

**Structure:** `facts` → `{taxonomy}` → `{metric}` → `units` → `{unit}` → `[data points]`

**Key fields per data point:**

| Field | Description |
|---|---|
| `start` | Period start date (absent for instant/point-in-time metrics like Assets) |
| `end` | Period end date (always present) |
| `val` | Reported value |
| `accn` | Accession number (links to the source filing) |
| `fy` | Fiscal year |
| `fp` | Fiscal period: `FY`, `Q1`, `Q2`, `Q3`, `Q4` |
| `form` | Filing form type: `10-K`, `10-Q`, etc. |
| `filed` | Date the filing was submitted to SEC |

**Parser must handle:**

- Multiple taxonomies (`us-gaap`, `ifrs-full`, `dei`)
- Multiple unit types per metric (`USD`, `shares`, `USD/shares`)
- Instant metrics (no `start` field — e.g., `Assets`, `StockholdersEquity`)
- Duration metrics (have both `start` and `end` — e.g., `Revenues`, `NetIncomeLoss`)
- Duplicate data points from amended filings (same metric + period, different accession number)

### XBRL Frames (`frames/us-gaap/{metric}/USD/CY{year}.json`)

```json
{
  "taxonomy": "us-gaap",
  "tag": "Revenues",
  "ccp": "CY2023",
  "uom": "USD",
  "label": "Revenues",
  "description": "...",
  "pts": 4283,
  "data": [
    {"accn": "0000320193-23-000106", "cik": 320193, "entityName": "Apple Inc.", "loc": "us-gaap/r/2", "end": "2023-09-30", "val": 383285000000},
    {"accn": "0000789019-23-000095", "cik": 789019, "entityName": "MICROSOFT CORP", "loc": "us-gaap/r/1", "end": "2023-06-30", "val": 211915000000}
  ]
}
```

Useful for cross-company comparisons (e.g., "show me revenue for all companies in 2023").

---

## XBRL Metric Alias Mapping

Users type friendly names; the parser maps them to XBRL tags. This table is the initial curated set for financial statement metrics. Store this mapping in `edgar/parser.py` or a dedicated `edgar/metrics.py`.

### Income Statement

| Friendly Name | XBRL Tag(s) | Notes |
|---|---|---|
| `revenue` | `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet` | Companies use different tags |
| `cost-of-revenue` | `CostOfRevenue`, `CostOfGoodsAndServicesSold` | |
| `gross-profit` | `GrossProfit` | |
| `operating-income` | `OperatingIncomeLoss` | |
| `net-income` | `NetIncomeLoss` | |
| `eps-basic` | `EarningsPerShareBasic` | Unit: `USD/shares` |
| `eps-diluted` | `EarningsPerShareDiluted` | Unit: `USD/shares` |

### Balance Sheet

| Friendly Name | XBRL Tag(s) | Notes |
|---|---|---|
| `total-assets` | `Assets` | Instant metric (no `start` date) |
| `total-liabilities` | `Liabilities` | Instant |
| `stockholders-equity` | `StockholdersEquity` | Instant |
| `cash` | `CashAndCashEquivalentsAtCarryingValue` | Instant |
| `current-assets` | `AssetsCurrent` | Instant |
| `current-liabilities` | `LiabilitiesCurrent` | Instant |

### Cash Flow Statement

| Friendly Name | XBRL Tag(s) | Notes |
|---|---|---|
| `operating-cash-flow` | `NetCashProvidedByUsedInOperatingActivities` | |
| `investing-cash-flow` | `NetCashProvidedByUsedInInvestingActivities` | |
| `financing-cash-flow` | `NetCashProvidedByUsedInFinancingActivities` | |
| `capex` | `PaymentsToAcquirePropertyPlantAndEquipment` | |

**Design note:** When a user queries `--metric revenue`, search for *all* XBRL tags in the alias list. Return whichever tag the company actually used. If multiple tags match for the same period, prefer the one with the most data points across filings.

---

## Database Schema

### `companies`

| Column | Type | Notes |
|---|---|---|
| cik | INTEGER | Primary key |
| name | TEXT | Company name (from `company_tickers.json` `title` field) |
| ticker | TEXT | Trading symbol |

**Indexes:** `ticker`, `name`.
**FTS5 virtual table:** `companies_fts` on `name` for fuzzy/prefix search (`ledgar search company --name "micro"` matches "MICROSOFT CORP").

> **Future columns:** `sic_code`, `state`, `exchange` may be added when a data source
> is integrated (e.g., the [company submissions endpoint](https://data.sec.gov/submissions/CIK{cik}.json)).

### `filings`

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key (autoincrement) |
| cik | INTEGER | FK → `companies.cik` |
| form_type | TEXT | `10-K`, `10-Q`, `8-K`, etc. |
| date_filed | TEXT | ISO 8601 date (`YYYY-MM-DD`) |
| accession_number | TEXT | Unique SEC filing identifier |
| file_path | TEXT | Relative path on EDGAR (from full-index) |

**Indexes:** `cik`, `form_type`, `date_filed`, `accession_number` (unique).

### `financial_facts`

| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key (autoincrement) |
| cik | INTEGER | FK → `companies.cik` |
| taxonomy | TEXT | `us-gaap`, `ifrs-full`, `dei` |
| metric | TEXT | XBRL tag name (e.g., `Revenues`, `NetIncomeLoss`, `Assets`) |
| label | TEXT | Human-readable label from XBRL (e.g., "Net Income (Loss)") |
| period_start | TEXT | ISO date, NULL for instant/point-in-time metrics |
| period_end | TEXT | ISO date (always present) |
| value | REAL | Reported numeric value |
| unit | TEXT | `USD`, `shares`, `USD/shares` |
| form_type | TEXT | Source filing type (`10-K`, `10-Q`) |
| accession_number | TEXT | Source filing accession number |
| fiscal_year | INTEGER | Fiscal year (from `fy` field) |
| fiscal_period | TEXT | `FY`, `Q1`, `Q2`, `Q3`, `Q4` (from `fp` field) |

**Indexes:** `cik` + `metric` (composite), `period_end`, `fiscal_year`, `accession_number`.

**Deduplication:** The combination of (`cik`, `metric`, `unit`, `period_end`, `accession_number`) should be unique. Use `INSERT OR IGNORE` or a unique constraint to handle amended filings that re-report the same data point.

### `metadata`

| Column | Type | Notes |
|---|---|---|
| key | TEXT | Primary key |
| value | TEXT | Stored as text; interpret per key |

**Standard keys:**

| Key | Example Value | Description |
|---|---|---|
| `last_tickers_download` | `2024-11-15T08:30:00Z` | Timestamp of last `company-tickers` download |
| `last_financials_download` | `2024-11-15T09:00:00Z` | Timestamp of last `companyfacts.zip` download |
| `last_index_download` | `2024-11-15T09:30:00Z` | Timestamp of last full-index download |
| `company_count` | `12453` | Number of rows in `companies` |
| `fact_count` | `48230157` | Number of rows in `financial_facts` |
| `schema_version` | `1` | For future schema migrations |

---

## Error Handling Strategy

### Exception Hierarchy

```
LedgarError (base)
├── ConfigError          — missing or invalid configuration
├── DataStoreError       — database missing, corrupt, or schema mismatch
│   └── NoDataError      — query attempted but relevant table is empty
├── DownloadError        — HTTP or network failure during EDGAR fetch
│   └── RateLimitError   — SEC rate limit hit (HTTP 429)
└── ParseError           — unexpected EDGAR JSON structure
```

All exceptions inherit from `LedgarError` so CLI entry points can catch broadly and produce actionable messages.

### Error Behavior

| Scenario | Behavior |
|---|---|
| No database file | `"No data store found. Run 'ledgar download company-tickers' to get started."` Exit code 2. |
| Empty table for query | `"No financial data loaded. Run 'ledgar download financials' first."` Exit code 2. |
| Network failure during download | Retry up to 3 times with exponential backoff. On final failure, report URL and HTTP status. Exit code 1. |
| SEC rate limit (429) | Pause for `Retry-After` header value (or 10 seconds), then retry. Log warning to stderr. |
| Corrupt/unparseable JSON | Log the file/CIK, skip it, continue with remaining files. Summarize skipped count at end. |
| Schema version mismatch | `"Database schema is outdated (v{old} → v{new}). Run 'ledgar download --rebuild' to recreate."` Exit code 2. |

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | User or input error (bad arguments, network failure) |
| 2 | Data error (missing DB, empty table, schema mismatch) |

---

## Data Refresh Strategy

### Idempotent Downloads

Each download command checks the `metadata` table before fetching:

1. Read `last_{source}_download` timestamp from `metadata`.
2. If absent → full download.
3. If present → warn user data exists, require `--force` to re-download.

### Incremental Updates

| Source | Incremental Approach |
|---|---|
| Company tickers | Re-download the full file (~200 KB, fast). Replace all rows. |
| Financial facts (bulk) | Re-download `companyfacts.zip`. Use `INSERT OR IGNORE` so existing rows are not duplicated. |
| Financial facts (single) | `ledgar download financials --cik <CIK>` fetches one company's JSON and upserts. |
| Filing index | Download only year/quarter combinations not already in `metadata`. |

### Full Rebuild

`ledgar download --rebuild` drops and recreates all tables, then runs a full download cycle. Use when schema version changes or data is suspected corrupt.

---

## Versioning

Single source of truth: `version` field in `pyproject.toml`.

At runtime, read via `importlib.metadata.version("ledgar")`. Exposed to the CLI through `click`'s `@click.version_option()`.

No `__version__` variable in source code — `pyproject.toml` is the canonical location.

---

## Configuration File

Config file location: `~/.ledgar/config.toml`

- **Read** with `tomllib` (stdlib, Python 3.11+).
- **Write** with `tomli-w` (third-party, minimal dependency).

The config file stores user-editable settings (`user-agent`, `data-dir`). Managed via `ledgar config set` / `ledgar config show` or by editing the file directly.

---

## Related Documents

| Document | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Build plan: decisions, command design, project layout, implementation order |
| [README.md](README.md) | End-user guide: installation, quickstart, usage examples |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Coding standards: Python style, testing, logging, CLI conventions |
| [CHANGELOG.md](CHANGELOG.md) | Version history in Keep a Changelog format |
