"""Search commands: query the local data store."""

import click

from ledgar.config import get_db_path
from ledgar.db.store import DataStore
from ledgar.edgar.parser import list_metrics, resolve_metric
from ledgar.formatters.table import format_companies_table, format_financials_table


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


@search.command()
@click.option("--cik", default=None, type=int, help="Company CIK number.")
@click.option("--ticker", default=None, help="Company ticker symbol.")
@click.option(
    "--metric",
    required=True,
    help=f"Financial metric ({', '.join(list_metrics()[:5])}, ...).",
)
@click.option(
    "--period",
    default=None,
    type=click.Choice(["annual", "quarterly"], case_sensitive=False),
    help="Filter by period type.",
)
@click.pass_context
def financials(
    ctx: click.Context,
    cik: int | None,
    ticker: str | None,
    metric: str,
    period: str | None,
):
    """Search financial data by company and metric."""
    if not cik and not ticker:
        raise click.UsageError("Provide --cik or --ticker.")
    if cik and ticker:
        raise click.UsageError("Provide --cik or --ticker, not both.")

    try:
        xbrl_tags = resolve_metric(metric)
    except ValueError as exc:
        raise click.ClickException(str(exc))

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
        if ticker:
            resolved_cik = store.get_cik_for_ticker(ticker)
            if resolved_cik is None:
                click.echo(f"Ticker '{ticker}' not found.", err=True)
                return
            cik = resolved_cik

        rows = store.search_financials(cik, xbrl_tags, period)

        if not rows:
            click.echo("No financial data found.", err=True)
            return

        format_financials_table(rows)
    finally:
        store.close()
