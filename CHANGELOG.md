# Changelog

> **Purpose of this file:** Version history tracking all notable changes to the project.
> Uses [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
>
> **Not for:** Build planning (see [AGENTS.md](AGENTS.md)), technical details
> (see [ARCHITECTURE.md](ARCHITECTURE.md)), or coding standards
> (see [CONTRIBUTING.md](CONTRIBUTING.md)).
>
> **Versioning:** This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Project planning documents: `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `README.md`
- Build order defined (9 incremental steps, see [AGENTS.md § Build Order](AGENTS.md#build-order))
- **Step 1**: Config module (`ledgar config set/show`), data directory setup, `ledgar info` command
- **Step 2**: `ledgar download company-tickers` — HTTP client with rate limiting, SQLite store, `companies` table
- **Step 3**: `ledgar search company --name/--ticker` — FTS5 prefix search, rich table output
- **Step 4**: `ledgar download financials` — bulk ZIP and single-CIK downloads, `financial_facts` table, `--rebuild` flag
- **Step 5**: `ledgar search financials --ticker/--cik --metric --period` — financial queries with metric aliases
- **Step 6**: `ledgar download full-index --year --quarter` — filing index download, `filings` table
- **Step 7**: `ledgar search filing --ticker/--cik --form-type --start-date --end-date` — filing search
- **Step 8**: Output formatters (`--output table|json|csv`) on all search commands
- **Step 9**: Error hierarchy (`ledgar/errors.py`), test suite (64 tests), pytest configuration

### Fixed

- Financial metric search now keeps the best matching XBRL alias per reported period instead of dropping newer history when a company changes tags over time
- Revenue search now recognizes `RevenueFromContractWithCustomerIncludingAssessedTax`, restoring newer histories for filers that moved off deprecated revenue tags

---

<!-- Entry template — copy this block for each new release:

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features

-->
