# Ledgar

> **Purpose of this file:** End-user guide — installation, quickstart, and usage examples.
>
> **Not for:** Build planning (see [AGENTS.md](AGENTS.md)), technical internals
> (see [ARCHITECTURE.md](ARCHITECTURE.md)), or contributor standards
> (see [CONTRIBUTING.md](CONTRIBUTING.md)).

Search SEC EDGAR financial data from your terminal. Ledgar downloads structured
XBRL filings to a local SQLite database so you can query income statements,
balance sheets, and cash flow data for any publicly traded U.S. company — offline,
instantly, and with no API keys.

---

## Prerequisites

- **Python 3.11+**
- **~2 GB free disk space** for the bulk XBRL download (compressed ~1.5 GB, database grows as data is imported)
- A SEC-compliant **User-Agent string** (your app name and email — [SEC policy](https://www.sec.gov/os/accessing-edgar-data))

---

## Installation

```bash
# Clone the repository
git clone https://github.com/<your-org>/ledgar.git
cd ledgar

# Install in development mode (creates the `ledgar` command)
pip install -e .
```

After installation, verify:

```bash
ledgar --version
ledgar --help
```

---

## Quickstart

Three commands to go from zero to your first query:

```bash
# 1. Configure your SEC-required User-Agent
ledgar config set user-agent "ledgar/1.0 (your-email@example.com)"

# 2. Download company ticker/CIK mapping (~200 KB)
ledgar download company-tickers

# 3. Search for a company
ledgar search company --name "Apple"
```

### Load financial data

```bash
# Download all structured financial data (~1.5 GB, one-time)
ledgar download financials

# Search for Apple's revenue
ledgar search financials --ticker AAPL --metric revenue --period annual
```

---

## Usage

### Download commands

```bash
# Download CIK ↔ ticker ↔ name mapping
ledgar download company-tickers

# Download bulk XBRL financial facts (all companies)
ledgar download financials

# Download financial facts for a single company (incremental)
ledgar download financials --cik 320193

# Download filing index for a specific period
ledgar download full-index --year 2024 --quarter 1

# Re-download data that already exists locally
ledgar download company-tickers --force

# Drop all tables and rebuild from scratch
ledgar download --rebuild
```

### Search commands

```bash
# Find a company by name (fuzzy match)
ledgar search company --name "Microsoft"

# Find a company by ticker
ledgar search company --ticker MSFT

# List filings for a company
ledgar search filing --cik 789019 --form-type 10-K

# Query financial metrics
ledgar search financials --ticker MSFT --metric revenue
ledgar search financials --ticker MSFT --metric net-income --period quarterly
ledgar search financials --cik 789019 --metric total-assets
```

### Output formats

All search commands support `--output` to control format:

```bash
ledgar search company --name "Tesla" --output table   # default, human-readable
ledgar search company --name "Tesla" --output json    # machine-readable
ledgar search company --name "Tesla" --output csv     # spreadsheet-friendly
```

Pipe-friendly: data goes to stdout, progress/warnings go to stderr.

```bash
# Pipe JSON output to jq
ledgar search financials --ticker AAPL --metric revenue --output json | jq '.[0]'

# Save CSV to file
ledgar search financials --ticker AAPL --metric revenue --output csv > aapl_revenue.csv
```

### Configuration

```bash
# Show current configuration
ledgar config show

# Set data directory (default: ~/.ledgar/data/)
ledgar config set data-dir /path/to/data

# Set User-Agent (required by SEC)
ledgar config set user-agent "ledgar/1.0 (you@example.com)"
```

### Data store info

```bash
# Print database location, last download date, record counts
ledgar info
```

---

## Global Options

| Option | Description |
|---|---|
| `--help` | Available at every command and subcommand level |
| `--version` | Print version and exit |
| `-v` / `--verbose` | Increase verbosity (repeatable: `-v` = INFO, `-vv` = DEBUG) |
| `--output [table\|json\|csv]` | Output format for search commands (default: `table`) |
| `--data-dir <path>` | Override default data directory for this invocation |

---

## How It Works

1. **Download** — Fetches bulk EDGAR data files from SEC and imports them into a local SQLite database at `~/.ledgar/data/ledgar.db`.
2. **Search** — Queries the local database. No network connection required after download.
3. **Display** — Formats results as tables, JSON, or CSV.

See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details on data sources, database schema, and XBRL parsing.

---

## License

[MIT](LICENSE)
