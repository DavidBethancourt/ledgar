"""Download commands: fetch EDGAR data into local store."""

import logging

import click

from ledgar.config import get_data_dir, get_db_path, get_user_agent
from ledgar.db.schema import create_tables, drop_all_tables
from ledgar.db.store import DataStore
from ledgar.edgar.bulk import download_companyfacts_zip, iter_companyfacts
from ledgar.edgar.client import EdgarClient
from ledgar.edgar.parser import (
    COMPANYFACTS_SINGLE_URL,
    COMPANY_TICKERS_URL,
    FULL_INDEX_URL,
    parse_company_facts,
    parse_company_tickers,
    parse_master_index,
)

log = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "--rebuild",
    is_flag=True,
    default=False,
    help="Drop all tables and recreate the database.",
)
@click.pass_context
def download(ctx: click.Context, rebuild: bool):
    """Download EDGAR data into local store."""
    if rebuild:
        data_dir = ctx.obj.get("data_dir")
        db_path = get_db_path(data_dir)
        if not db_path.exists():
            click.echo("No database to rebuild.", err=True)
            return
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        drop_all_tables(conn)
        create_tables(conn)
        conn.close()
        click.echo("Database rebuilt. Run download commands to re-populate.")


@download.command("company-tickers")
@click.option("--force", is_flag=True, help="Re-download even if data exists.")
@click.pass_context
def company_tickers(ctx: click.Context, force: bool):
    """Download CIK/ticker/name mapping from SEC EDGAR."""
    data_dir = ctx.obj.get("data_dir")
    db_path = get_db_path(data_dir)
    store = DataStore(str(db_path))

    try:
        last_dl = store.get_metadata("last_tickers_download")
        if last_dl and not force:
            click.echo(
                f"Company tickers already downloaded ({last_dl}). "
                "Use --force to re-download.",
                err=True,
            )
            return

        user_agent = get_user_agent()
        client = EdgarClient(user_agent)

        click.echo("Downloading company tickers...", err=True)
        data = client.fetch_json(COMPANY_TICKERS_URL)
        rows = parse_company_tickers(data)

        count = store.insert_companies(rows)
        store.set_metadata_now("last_tickers_download")
        store.set_metadata("company_count", str(count))

        click.echo(f"Downloaded {count:,} companies.", err=True)
    finally:
        store.close()


@download.command("financials")
@click.option("--cik", default=None, type=int, help="Download for a single company CIK.")
@click.option("--force", is_flag=True, help="Re-download even if data exists.")
@click.pass_context
def financials(ctx: click.Context, cik: int | None, force: bool):
    """Download XBRL financial facts (bulk or single company)."""
    data_dir_override = ctx.obj.get("data_dir")
    db_path = get_db_path(data_dir_override)
    store = DataStore(str(db_path))

    try:
        if cik:
            _download_single_financials(store, cik, force)
        else:
            _download_bulk_financials(store, data_dir_override, force)
    finally:
        store.close()


def _download_single_financials(store: DataStore, cik: int, force: bool) -> None:
    """Download financial facts for a single company."""
    last_dl = store.get_metadata("last_financials_download")
    if last_dl and not force:
        click.echo(
            f"Financial data already downloaded ({last_dl}). "
            "Use --force to re-download.",
            err=True,
        )
        return

    user_agent = get_user_agent()
    client = EdgarClient(user_agent)

    url = COMPANYFACTS_SINGLE_URL.format(cik=cik)
    click.echo(f"Downloading financials for CIK {cik}...", err=True)
    data = client.fetch_json(url)
    rows = parse_company_facts(cik, data)

    count = store.insert_financial_facts(rows)
    click.echo(f"Loaded {count:,} financial facts for CIK {cik}.", err=True)


def _download_bulk_financials(
    store: DataStore, data_dir_override: str | None, force: bool
) -> None:
    """Download bulk companyfacts.zip and load all financial facts."""
    last_dl = store.get_metadata("last_financials_download")
    if last_dl and not force:
        click.echo(
            f"Financial data already downloaded ({last_dl}). "
            "Use --force to re-download.",
            err=True,
        )
        return

    user_agent = get_user_agent()
    client = EdgarClient(user_agent)
    data_dir = get_data_dir(data_dir_override)

    zip_path = download_companyfacts_zip(client, data_dir)

    total_facts = 0
    total_companies = 0
    batch = []
    batch_size = 10_000

    for company_cik, data in iter_companyfacts(zip_path):
        rows = parse_company_facts(company_cik, data)
        batch.extend(rows)
        total_companies += 1

        if len(batch) >= batch_size:
            total_facts += store.insert_financial_facts(batch)
            batch = []

    if batch:
        total_facts += store.insert_financial_facts(batch)

    store.set_metadata_now("last_financials_download")
    store.set_metadata("fact_count", str(total_facts))

    click.echo(
        f"Loaded {total_facts:,} financial facts from {total_companies:,} companies.",
        err=True,
    )


@download.command("full-index")
@click.option("--year", default=None, type=int, help="Filing year (e.g., 2024).")
@click.option(
    "--quarter", default=None, type=click.IntRange(1, 4), help="Filing quarter (1-4)."
)
@click.option("--force", is_flag=True, help="Re-download even if data exists.")
@click.pass_context
def full_index(ctx: click.Context, year: int | None, quarter: int | None, force: bool):
    """Download filing index from SEC EDGAR."""
    from datetime import datetime, timezone

    if year is None:
        now = datetime.now(timezone.utc)
        year = now.year
        quarter = quarter or ((now.month - 1) // 3 + 1)
    elif quarter is None:
        raise click.UsageError("--quarter is required when --year is specified.")

    data_dir_override = ctx.obj.get("data_dir")
    db_path = get_db_path(data_dir_override)
    store = DataStore(str(db_path))

    try:
        meta_key = f"index_{year}_Q{quarter}"
        last_dl = store.get_metadata(meta_key)
        if last_dl and not force:
            click.echo(
                f"Index for {year} Q{quarter} already downloaded ({last_dl}). "
                "Use --force to re-download.",
                err=True,
            )
            return

        user_agent = get_user_agent()
        client = EdgarClient(user_agent)

        url = FULL_INDEX_URL.format(year=year, quarter=quarter)
        click.echo(f"Downloading filing index for {year} Q{quarter}...", err=True)

        raw = client.fetch_bytes(url)
        text = raw.decode("utf-8", errors="replace")
        rows = parse_master_index(text)

        count = store.insert_filings(rows)
        store.set_metadata_now(meta_key)
        store.set_metadata_now("last_index_download")

        click.echo(f"Loaded {count:,} filings for {year} Q{quarter}.", err=True)
    finally:
        store.close()
