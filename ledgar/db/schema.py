"""Database schema: table definitions, indexes, FTS5, migrations."""

import logging
import sqlite3

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables, indexes, and FTS5 virtual tables if they don't exist."""
    cur = conn.cursor()

    # --- companies ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            cik     INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            ticker  TEXT
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies (ticker)"
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies (name)")

    # FTS5 virtual table for fuzzy/prefix company name search
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS companies_fts
        USING fts5(name, content='companies', content_rowid='cik')
    """)

    # --- filings ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS filings (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            cik              INTEGER NOT NULL,
            form_type        TEXT NOT NULL,
            date_filed       TEXT NOT NULL,
            accession_number TEXT NOT NULL,
            file_path        TEXT,
            FOREIGN KEY (cik) REFERENCES companies(cik)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings (cik)")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_filings_form_type ON filings (form_type)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_filings_date_filed ON filings (date_filed)"
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_filings_accession "
        "ON filings (accession_number)"
    )

    # --- financial_facts ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS financial_facts (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            cik              INTEGER NOT NULL,
            taxonomy         TEXT NOT NULL,
            metric           TEXT NOT NULL,
            label            TEXT,
            period_start     TEXT,
            period_end       TEXT NOT NULL,
            value            REAL NOT NULL,
            unit             TEXT NOT NULL,
            form_type        TEXT,
            accession_number TEXT,
            fiscal_year      INTEGER,
            fiscal_period    TEXT,
            FOREIGN KEY (cik) REFERENCES companies(cik)
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_facts_cik_metric "
        "ON financial_facts (cik, metric)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_facts_period_end "
        "ON financial_facts (period_end)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_facts_fiscal_year "
        "ON financial_facts (fiscal_year)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_facts_accession "
        "ON financial_facts (accession_number)"
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_dedup "
        "ON financial_facts (cik, metric, unit, period_end, accession_number)"
    )

    # --- metadata ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Set schema version if not already set
    cur.execute(
        "INSERT OR IGNORE INTO metadata (key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )

    conn.commit()
    log.debug("Database schema initialized (version %d)", SCHEMA_VERSION)


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """Drop all tables for a full rebuild."""
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS financial_facts")
    cur.execute("DROP TABLE IF EXISTS filings")
    cur.execute("DROP TABLE IF EXISTS companies_fts")
    cur.execute("DROP TABLE IF EXISTS companies")
    cur.execute("DROP TABLE IF EXISTS metadata")
    conn.commit()
    log.info("All tables dropped")
