# Ledgar — EDGAR Financial Data CLI

> **Purpose of this file:** AI agent and developer build plan — decisions, command design,
> project layout, and implementation order. This is the "what to build and in what sequence" document.
>
> **Not for:** EDGAR data details or JSON structures (see [ARCHITECTURE.md](ARCHITECTURE.md)),
> coding standards or testing approach (see [CONTRIBUTING.md](CONTRIBUTING.md)),
> end-user installation and usage (see [README.md](README.md)).
>
> **Maintenance rule — keep related documents in sync.** When a change to this project
> affects any of the documents below, update them in the same step:
>
> | If you change… | Also update… |
> |---|---|
> | Command names, options, or subcommands | [README.md](README.md) (Usage section) |
> | Schema (tables, columns, indexes) | [ARCHITECTURE.md](ARCHITECTURE.md) (Database Schema section) |
> | EDGAR data sources or JSON structures | [ARCHITECTURE.md](ARCHITECTURE.md) (EDGAR Data Sources section) |
> | Error handling, data flow, or refresh strategy | [ARCHITECTURE.md](ARCHITECTURE.md) (relevant section) |
> | Coding style, testing, logging, or CLI conventions | [CONTRIBUTING.md](CONTRIBUTING.md) (relevant section) |
> | Project layout or new modules | [ARCHITECTURE.md](ARCHITECTURE.md) (Data Flow) and this file (Project Layout) |
> | Any shipped feature or bug fix | [CHANGELOG.md](CHANGELOG.md) (Unreleased section) |

## Overview

`ledgar` is a command-line utility that searches a local copy of SEC EDGAR data to retrieve financial information for any publicly traded company. The app does **not** maintain a live connection to EDGAR at query time. A one-time (or periodic) bulk download populates a local SQLite data store, and all searches run against that local store.

### Current Scope

The initial focus is on **current and historical financial statement data** (income statements, balance sheets, cash flow statements) sourced from structured XBRL filings. The architecture should accommodate future expansion into other EDGAR data sets (insider transactions, institutional holdings, etc.).

---

## EDGAR Data Sources

See [ARCHITECTURE.md § EDGAR Data Sources](ARCHITECTURE.md#edgar-data-sources) for the full source table, documentation links, JSON response structures, and XBRL metric alias mapping.

Key points for build planning:

- **Bulk download** (`companyfacts.zip`, ~1.5 GB) is the primary data source for financial facts.
- **Company tickers JSON** is the simplest download and the starting point (Build Step 2).
- **SEC rate limit**: 10 req/sec, `User-Agent` header required.
- **CIK zero-padding**: API URLs require CIKs padded to 10 digits (e.g., `CIK0000320193`).

---

## CLI Framework

### Choice: `click`

- Declarative command/subcommand structure via decorators
- Auto-generated `--help` at every level for discoverability
- Built-in input validation, type coercion, and prompting
- Supports command groups, aliases, and plugin-style extensibility
- Widely adopted (used by `pip`, `flask`, AWS CLI v2 uses similar patterns)

Alternative: `typer` (built on `click`, uses type hints). Either is solid.

---

## Command Structure

### Top-Level Groups

```
ledgar download   — one-time fetch from EDGAR into local store
ledgar search     — query the local store
ledgar config     — manage app configuration
ledgar info       — print data store location, last download date, record counts
```

### Download Commands

```
ledgar download company-tickers [--force]                 # CIK/ticker/name mapping
ledgar download financials [--cik <CIK>] [--force]       # XBRL company facts (bulk or single)
ledgar download full-index [--year <YYYY>] [--quarter <1-4>] [--force]  # filing index
ledgar download --rebuild                                # drop all tables and re-download
```

### Search Commands

```
ledgar search company --name <name>                      # fuzzy company lookup
ledgar search company --ticker <ticker>                  # exact ticker lookup
ledgar search filing --cik <CIK> [--form-type 10-K|10-Q] [--start-date] [--end-date]
ledgar search financials --cik <CIK> [--metric revenue|net-income|total-assets|...]
ledgar search financials --ticker <AAPL> [--metric ...] [--period annual|quarterly]
```

### Config Commands

```
ledgar config set <key> <value>      # e.g., data-dir, user-agent
ledgar config show                   # print current configuration
```

### Global Options

| Option | Description |
|---|---|
| `--help` | Available at every command/group level |
| `--version` | Print version and exit |
| `-v` / `--verbose` | Increase verbosity (repeatable: `-v` = INFO, `-vv` = DEBUG) |
| `--output [table\|json\|csv]` | Output format (default: table) |
| `--data-dir <path>` | Override default data directory |

---

## Local Data Store

### Choice: SQLite

- Zero infrastructure, single file, ships with Python (`sqlite3`)
- Handles millions of EDGAR index rows comfortably
- Full SQL for complex financial queries
- FTS5 (full-text search) for company name lookups
- Optional: `sqlite-utils` for convenient schema management

### Default Location

```
~/.ledgar/data/ledgar.db
```

Overridable via `ledgar config set data-dir <path>` or `--data-dir` flag.

### Schema

Four tables: `companies`, `filings`, `financial_facts`, `metadata`.

See [ARCHITECTURE.md § Database Schema](ARCHITECTURE.md#database-schema) for full column definitions, indexes, and FTS5 configuration.

---

## Project Layout

```
ledgar/
├── ledgar.py              # CLI entry point (click group)
├── commands/
│   ├── __init__.py
│   ├── download.py        # download command group
│   ├── search.py          # search command group
│   └── config.py          # config command group
├── db/
│   ├── __init__.py
│   ├── schema.py          # table definitions, migrations
│   ├── store.py           # insert/query abstraction over sqlite
│   └── fts.py             # full-text search helpers
├── edgar/
│   ├── __init__.py
│   ├── client.py          # HTTP fetching from SEC (requests + rate limit)
│   ├── parser.py          # parse XBRL JSON, index files
│   └── bulk.py            # handle companyfacts.zip download + extract
├── formatters/
│   ├── __init__.py
│   ├── table.py           # rich/tabulate table output
│   ├── json_fmt.py        # JSON output
│   └── csv_fmt.py         # CSV output
├── config.py              # app config (data dir, user-agent, defaults)
├── pyproject.toml         # packaging, [project.scripts] entry point
└── tests/
    ├── __init__.py
    ├── conftest.py        # shared fixtures (sample DB, mock HTTP, CLI runner)
    ├── fixtures/          # static test data (trimmed SEC JSON samples)
    ├── test_config.py
    ├── test_download.py
    ├── test_search.py
    ├── test_store.py
    ├── test_parser.py
    └── test_formatters.py
```

Use `pyproject.toml` with a `[project.scripts]` entry so `pip install .` or `pip install -e .` creates the `ledgar` command globally.

---

## Key Libraries

| Library | Purpose |
|---|---|
| `click` | CLI framework, command groups, help generation |
| `requests` | HTTP client for EDGAR downloads |
| `rich` | Terminal tables, progress bars, colored output |
| `tomli-w` | TOML writing for config file (companion to stdlib `tomllib`) |
| `sqlite-utils` | Optional — convenient SQLite wrapper for schema/insert |

All are well-maintained, pip-installable, no heavy dependencies.

---

## CLI Best Practices

See [CONTRIBUTING.md § CLI Conventions](CONTRIBUTING.md#cli-conventions) for the full best-practices table covering help text, exit codes, stderr/stdout separation, output formats, progress bars, and error messages.

---

## Build Order

| Step | Deliverable | Validates |
|---|---|---|
| 1 | Config + data directory setup (`ledgar config`) | Path management, config persistence |
| 2 | `ledgar download company-tickers` | HTTP client, SQLite insert, `companies` table |
| 3 | `ledgar search company --name` | Full pipeline: download → store → query → display |
| 4 | `ledgar download financials` (bulk XBRL) | Bulk ZIP handling, `financial_facts` table |
| 5 | `ledgar search financials --ticker --metric` | Financial queries, period filtering |
| 6 | `ledgar download full-index` | `filings` table, year/quarter filtering |
| 7 | `ledgar search filing` | Filing index queries |
| 8 | Output formatters (`--output json/csv/table`) | Multi-format output |
| 9 | Polish | Error handling, progress bars, idempotency, tests |

Each step produces a working increment. Step 3 is the first end-to-end slice.

---

## Related Documents

| Document | Purpose |
|---|---|
| [README.md](README.md) | End-user guide: installation, quickstart, usage examples |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical deep dive: EDGAR sources, JSON structures, schema, data flow, error handling |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Coding standards: Python style, testing, logging, CLI conventions |
| [CHANGELOG.md](CHANGELOG.md) | Version history in Keep a Changelog format |
