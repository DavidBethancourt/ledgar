# Contributing

> **Purpose of this file:** Coding standards, testing approach, logging conventions,
> and CLI conventions for anyone implementing or modifying ledgar code. This is the
> "how to write code for this project" document.
>
> **Not for:** What to build or in what order (see [AGENTS.md](AGENTS.md)),
> EDGAR data details or schema (see [ARCHITECTURE.md](ARCHITECTURE.md)),
> or end-user usage (see [README.md](README.md)).

---

## Python Version

**Minimum: Python 3.11**

Required for `tomllib` (stdlib TOML parser), `match`/`case` statements, `typing` improvements (`X | Y` union syntax), and `importlib.metadata` without backport.

---

## Code Style

### Formatting

- **Formatter:** `black` (default settings, line length 88)
- **Linter:** `ruff` (replaces `flake8`, `isort`, and more)
- **Import order:** stdlib → third-party → local, enforced by `ruff`

Run before committing:

```bash
black ledgar/ tests/
ruff check ledgar/ tests/ --fix
```

### Type Hints

Use type hints on all public function signatures. Internal/private helpers can omit them if trivial.

```python
def format_cik(cik: int) -> str:
    """Zero-pad a CIK to 10 digits for SEC API URLs."""
    return f"CIK{cik:010d}"
```

### Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `json_fmt.py`, `store.py` |
| Functions | `snake_case` | `download_company_tickers()` |
| Classes | `PascalCase` | `DataStoreError` |
| Constants | `UPPER_SNAKE` | `DEFAULT_DATA_DIR` |
| CLI commands | `kebab-case` | `company-tickers`, `full-index` |
| CLI options | `--kebab-case` | `--form-type`, `--data-dir` |

### Docstrings

Use Google-style docstrings. Click command docstrings double as `--help` text, so write them as user-facing descriptions (imperative mood, concise).

```python
@cli.command()
def company_tickers():
    """Download CIK/ticker/name mapping from SEC EDGAR."""
```

### Comments

Add comments only when the *why* is not obvious from the code. Do not restate what the code does.

---

## Project Structure Conventions

### Module Responsibilities

| Module | Allowed Dependencies | Responsibility |
|---|---|---|
| `commands/` | `db/`, `edgar/`, `formatters/`, `config` | CLI command definitions (thin — delegate to other modules) |
| `db/` | `sqlite3` only | Database access, schema, queries |
| `edgar/` | `requests`, `json`, `zipfile` | HTTP client, JSON parsing, bulk download |
| `formatters/` | `rich`, `json`, `csv` | Output rendering |
| `config.py` | `pathlib`, `tomllib`, `tomli_w` | Configuration read/write |

**Rule:** `db/` must not import from `edgar/`. `edgar/` must not import from `db/`. Commands in `commands/` wire them together.

---

## CLI Conventions

| Practice | Implementation |
|---|---|
| **Consistent `--help`** | `click` auto-generates from docstrings at every command level |
| **Exit codes** | `0` = success, `1` = user/input error, `2` = data error (see [ARCHITECTURE.md § Error Handling](ARCHITECTURE.md#error-handling-strategy)) |
| **Stderr for diagnostics** | Use `click.echo(..., err=True)` for progress messages, warnings, and errors |
| **Stdout for data** | All query results go to stdout so they can be piped or redirected |
| **Progress bars** | `rich.progress` for downloads; `click.progressbar` acceptable for simpler cases |
| **Output formats** | Global `--output [table\|json\|csv]` option on the `search` command group |
| **Colored output** | Use `rich` for tables and highlighting; degrade gracefully when stdout is not a TTY |
| **Idempotent downloads** | Check `metadata` table before fetching; require `--force` to re-download |
| **Rate limiting** | SEC allows 10 req/sec max — enforce via `time.sleep()` throttle in `edgar/client.py` |
| **Config file** | `~/.ledgar/config.toml` — editable via `ledgar config` commands or by hand |
| **Actionable errors** | Always tell the user what to do next, e.g., `"No local data found. Run 'ledgar download company-tickers' first."` |

### Adding a New Command

1. Create or edit the appropriate file in `commands/` (e.g., `commands/search.py`).
2. Define a `click` command or group with a docstring (this becomes `--help` text).
3. Delegate to `db/` for queries or `edgar/` for downloads — keep the command function thin.
4. Wire output through `formatters/` using the `--output` context option.
5. Add a test in `tests/`.
6. Update [AGENTS.md](AGENTS.md) command structure if the command is new.

---

## Testing

### Framework

**pytest** with these plugins:

| Plugin | Purpose |
|---|---|
| `pytest` | Test runner |
| `click.testing.CliRunner` | Invoke CLI commands in-process, capture output |
| `responses` | Mock HTTP requests to SEC (no live calls in tests) |
| `tmp_path` (built-in) | Temporary directories for test databases |

### Test Organization

```
tests/
├── __init__.py
├── conftest.py          # shared fixtures (sample DB, mock HTTP, CLI runner)
├── fixtures/            # static test data files
│   ├── company_tickers_sample.json
│   ├── companyfacts_320193_sample.json
│   └── frames_revenue_2023_sample.json
├── test_config.py       # config read/write/defaults
├── test_download.py     # download commands (mocked HTTP → real SQLite)
├── test_search.py       # search commands (pre-loaded SQLite → output)
├── test_store.py        # db/store.py unit tests
├── test_parser.py       # edgar/parser.py unit tests
└── test_formatters.py   # output formatting
```

### Fixture Strategy

- **`tests/fixtures/`** contains small, real-shaped JSON files trimmed from actual SEC responses. Keep them minimal (2–3 companies, 2–3 metrics each).
- **`conftest.py`** provides a `sample_db` fixture that creates an in-memory SQLite database pre-loaded from fixture JSON files.
- **No live HTTP calls.** All tests that involve `edgar/client.py` must use `responses` to mock SEC endpoints.

### Running Tests

```bash
pytest                         # all tests
pytest tests/test_search.py    # single file
pytest -k "test_revenue"       # name pattern
pytest --tb=short              # shorter tracebacks
```

### What to Test

| Layer | What to Assert |
|---|---|
| `edgar/parser.py` | Correct extraction of metrics, handling of instant vs. duration, multiple units |
| `db/store.py` | Insert + query round-trip, deduplication, FTS search results |
| `commands/` | Exit codes, stdout content, stderr warnings (via `CliRunner`) |
| `formatters/` | Table/JSON/CSV output matches expected shape |

---

## Logging

### Verbosity Levels

Controlled via a global `-v` / `--verbose` flag (repeatable):

| Flag | Level | What is logged |
|---|---|---|
| (default) | WARNING | Errors and warnings only |
| `-v` | INFO | Progress summaries (e.g., "Downloaded 12,453 companies") |
| `-vv` | DEBUG | HTTP request URLs, SQL queries, parse details |

### Implementation

Use Python's built-in `logging` module. Configure in the CLI entry point based on verbosity count:

```python
import logging

verbosity_map = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
logging.basicConfig(
    level=verbosity_map.get(verbose, logging.DEBUG),
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
)
```

All log output goes to **stderr** (never stdout) so it does not interfere with piped data.

---

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short description>

<optional body>
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`
**Scopes:** `cli`, `db`, `edgar`, `fmt`, `config`

Examples:

```
feat(edgar): add bulk companyfacts.zip download
fix(db): handle NULL period_start for instant metrics
docs(readme): add quickstart section
test(search): add revenue query tests with sample fixtures
```

---

## Related Documents

| Document | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Build plan: decisions, command design, project layout, implementation order |
| [README.md](README.md) | End-user guide: installation, quickstart, usage examples |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical deep dive: EDGAR sources, JSON structures, schema, data flow |
| [CHANGELOG.md](CHANGELOG.md) | Version history in Keep a Changelog format |
