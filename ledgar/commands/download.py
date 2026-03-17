"""Download commands: fetch EDGAR data into local store."""

import logging

import click

from ledgar.config import get_db_path, get_user_agent
from ledgar.db.schema import create_tables, drop_all_tables
from ledgar.db.store import DataStore
from ledgar.edgar.client import EdgarClient
from ledgar.edgar.parser import COMPANY_TICKERS_URL, parse_company_tickers

log = logging.getLogger(__name__)


@click.group()
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
