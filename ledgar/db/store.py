"""Data store: insert/query abstraction over SQLite."""

import logging
import sqlite3
from datetime import datetime, timezone

from ledgar.db.schema import create_tables

log = logging.getLogger(__name__)


class DataStore:
    """SQLite data store for EDGAR data."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        create_tables(self.conn)

    def close(self) -> None:
        self.conn.close()

    # --- Metadata ---

    def get_metadata(self, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM metadata WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def set_metadata_now(self, key: str) -> None:
        """Set a metadata key to the current UTC timestamp."""
        self.set_metadata(key, datetime.now(timezone.utc).isoformat())

    # --- Companies ---

    def insert_companies(self, rows: list[tuple[int, str, str]]) -> int:
        """Insert or replace companies. Returns count inserted."""
        self.conn.executemany(
            "INSERT OR REPLACE INTO companies (cik, name, ticker) VALUES (?, ?, ?)",
            rows,
        )
        # Rebuild standalone FTS index from the deduplicated companies table
        self.conn.execute("DELETE FROM companies_fts")
        self.conn.execute(
            "INSERT INTO companies_fts(rowid, name) SELECT cik, name FROM companies"
        )
        self.conn.commit()
        count = self.conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        log.info("Inserted %d companies, FTS index rebuilt", count)
        return count

    def search_companies_by_name(self, query: str) -> list[dict]:
        """FTS5 prefix search on company name."""
        fts_query = query.strip() + "*"
        rows = self.conn.execute(
            "SELECT c.cik, c.name, c.ticker "
            "FROM companies_fts f "
            "JOIN companies c ON c.cik = f.rowid "
            "WHERE companies_fts MATCH ? "
            "LIMIT 25",
            (fts_query,),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_company_by_ticker(self, ticker: str) -> dict | None:
        """Exact ticker lookup (case-insensitive)."""
        row = self.conn.execute(
            "SELECT cik, name, ticker FROM companies WHERE ticker = ? COLLATE NOCASE",
            (ticker,),
        ).fetchone()
        return dict(row) if row else None

    def get_cik_for_ticker(self, ticker: str) -> int | None:
        """Resolve a ticker to a CIK."""
        row = self.conn.execute(
            "SELECT cik FROM companies WHERE ticker = ? COLLATE NOCASE",
            (ticker,),
        ).fetchone()
        return row[0] if row else None

    # --- Financial Facts ---

    def insert_financial_facts(self, rows: list[dict]) -> int:
        """Bulk insert financial facts. Returns count inserted."""
        if not rows:
            return 0
        self.conn.executemany(
            """INSERT OR IGNORE INTO financial_facts
            (cik, taxonomy, metric, label, period_start, period_end,
             value, unit, form_type, accession_number, fiscal_year, fiscal_period)
            VALUES (:cik, :taxonomy, :metric, :label, :period_start, :period_end,
                    :value, :unit, :form_type, :accession_number, :fiscal_year, :fiscal_period)
            """,
            rows,
        )
        self.conn.commit()
        count = len(rows)
        log.debug("Inserted batch of %d financial facts", count)
        return count

    def search_financials(
        self,
        cik: int,
        xbrl_tags: list[str],
        period: str | None = None,
    ) -> list[dict]:
        """Query financial facts for a company and metric tags."""
        placeholders = ",".join("?" for _ in xbrl_tags)
        sql = (
            f"SELECT * FROM financial_facts "
            f"WHERE cik = ? AND metric IN ({placeholders})"
        )
        params: list = [cik, *xbrl_tags]

        if period == "annual":
            sql += " AND fiscal_period = 'FY'"
        elif period == "quarterly":
            sql += " AND fiscal_period IN ('Q1', 'Q2', 'Q3', 'Q4')"

        sql += " ORDER BY fiscal_year DESC, period_end DESC"

        rows = self.conn.execute(sql, params).fetchall()
        results = [dict(r) for r in rows]

        # Tag preference: if multiple tags returned, keep only the most common one
        if results and len(set(r["metric"] for r in results)) > 1:
            from collections import Counter

            tag_counts = Counter(r["metric"] for r in results)
            best_tag = tag_counts.most_common(1)[0][0]
            results = [r for r in results if r["metric"] == best_tag]

        return results

    # --- Filings ---

    def insert_filings(self, rows: list[dict]) -> int:
        """Bulk insert filings. Returns count inserted."""
        if not rows:
            return 0
        self.conn.executemany(
            """INSERT OR IGNORE INTO filings
            (cik, form_type, date_filed, accession_number, file_path)
            VALUES (:cik, :form_type, :date_filed, :accession_number, :file_path)
            """,
            rows,
        )
        self.conn.commit()
        count = len(rows)
        log.debug("Inserted batch of %d filings", count)
        return count

    def search_filings(
        self,
        cik: int,
        form_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """Query filings for a company with optional filters."""
        sql = "SELECT * FROM filings WHERE cik = ?"
        params: list = [cik]

        if form_type:
            sql += " AND form_type = ?"
            params.append(form_type)
        if start_date:
            sql += " AND date_filed >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date_filed <= ?"
            params.append(end_date)

        sql += " ORDER BY date_filed DESC"

        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
