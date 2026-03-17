"""Search commands: query the local data store."""

import click

from ledgar.config import get_db_path
from ledgar.db.store import DataStore
from ledgar.formatters.table import format_companies_table


@click.group()
@click.pass_context
def search(ctx: click.Context):
    """Query the local EDGAR data store."""


@search.command()
@click.option("--name", default=None, help="Fuzzy search by company name.")
@click.option("--ticker", default=None, help="Exact ticker lookup.")
@click.pass_context
def company(ctx: click.Context, name: str | None, ticker: str | None):
    """Search for a company by name or ticker."""
    if not name and not ticker:
        raise click.UsageError("Provide --name or --ticker.")
    if name and ticker:
        raise click.UsageError("Provide --name or --ticker, not both.")

    data_dir = ctx.obj.get("data_dir")
    db_path = get_db_path(data_dir)
    if not db_path.exists():
        click.echo(
            "No data store found. Run 'ledgar download company-tickers' first.",
            err=True,
        )
        raise SystemExit(2)

    store = DataStore(str(db_path))
    try:
        if name:
            rows = store.search_companies_by_name(name)
        else:
            result = store.search_company_by_ticker(ticker)
            rows = [result] if result else []

        if not rows:
            click.echo("No companies found.", err=True)
            return

        format_companies_table(rows)
    finally:
        store.close()
