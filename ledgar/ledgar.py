"""Ledgar CLI entry point."""

import importlib.metadata
import logging
import sqlite3
import sys

import click

from ledgar.commands.config import config
from ledgar.commands.download import download
from ledgar.config import get_db_path
from ledgar.db.schema import create_tables


@click.group()
@click.version_option(version=importlib.metadata.version("ledgar"), prog_name="ledgar")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v = INFO, -vv = DEBUG).",
)
@click.option(
    "--data-dir",
    default=None,
    type=click.Path(),
    help="Override default data directory.",
)
@click.pass_context
def cli(ctx: click.Context, verbose: int, data_dir: str | None):
    """Search SEC EDGAR financial data from your terminal."""
    verbosity_map = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(
        level=verbosity_map.get(verbose, logging.DEBUG),
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    ctx.ensure_object(dict)
    ctx.obj["data_dir"] = data_dir


cli.add_command(config)
cli.add_command(download)


@cli.command()
@click.pass_context
def info(ctx: click.Context):
    """Print data store location, last download date, and record counts."""
    data_dir = ctx.obj.get("data_dir")
    db_path = get_db_path(data_dir)

    if not db_path.exists():
        click.echo(f"Database: {db_path} (does not exist)")
        click.echo("No data store found. Run 'ledgar download company-tickers' to get started.")
        ctx.exit(2)
        return

    conn = sqlite3.connect(str(db_path))
    create_tables(conn)

    def get_meta(key: str) -> str:
        row = conn.execute(
            "SELECT value FROM metadata WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else "(none)"

    def count_rows(table: str) -> int:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
        return row[0] if row else 0

    click.echo(f"Database:          {db_path}")
    click.echo(f"Schema version:    {get_meta('schema_version')}")
    click.echo(f"Companies:         {count_rows('companies'):,}")
    click.echo(f"Financial facts:   {count_rows('financial_facts'):,}")
    click.echo(f"Filings:           {count_rows('filings'):,}")
    click.echo(f"Last tickers DL:   {get_meta('last_tickers_download')}")
    click.echo(f"Last financials DL:{get_meta('last_financials_download')}")
    click.echo(f"Last index DL:     {get_meta('last_index_download')}")

    conn.close()
