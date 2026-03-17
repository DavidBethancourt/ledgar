"""Rich table output formatter."""

from rich.console import Console
from rich.table import Table


def format_companies_table(rows: list[dict]) -> None:
    """Render companies as a rich table to stdout."""
    table = Table(title="Companies")
    table.add_column("CIK", justify="right", style="cyan")
    table.add_column("Ticker", style="green")
    table.add_column("Name", style="white")

    for row in rows:
        table.add_row(str(row["cik"]), row.get("ticker", ""), row.get("name", ""))

    console = Console()
    console.print(table)


def format_financials_table(rows: list[dict]) -> None:
    """Render financial facts as a rich table to stdout."""
    table = Table(title="Financial Data")
    table.add_column("Period End", style="cyan")
    table.add_column("Context FY", justify="right", style="cyan")
    table.add_column("Period", style="green")
    table.add_column("Value", justify="right", style="white bold")
    table.add_column("Unit", style="dim")
    table.add_column("Metric", style="dim")
    table.add_column("Form", style="dim")
    table.add_column("Filed", style="dim")

    for row in rows:
        val = row.get("value")
        if val is not None and row.get("unit") == "USD":
            val_str = f"${val:,.0f}"
        elif val is not None and row.get("unit") == "USD/shares":
            val_str = f"${val:,.2f}"
        elif val is not None:
            val_str = f"{val:,.0f}"
        else:
            val_str = ""
        table.add_row(
            row.get("period_end", ""),
            str(row.get("fiscal_year", "")),
            row.get("fiscal_period", ""),
            val_str,
            row.get("unit", ""),
            row.get("metric", ""),
            row.get("form_type", ""),
            row.get("accession_number", ""),
        )

    console = Console()
    console.print(table)


def format_filings_table(rows: list[dict]) -> None:
    """Render filings as a rich table to stdout."""
    table = Table(title="Filings")
    table.add_column("Form Type", style="green")
    table.add_column("Date Filed", style="cyan")
    table.add_column("Accession Number", style="white")
    table.add_column("File Path", style="dim")

    for row in rows:
        table.add_row(
            row.get("form_type", ""),
            row.get("date_filed", ""),
            row.get("accession_number", ""),
            row.get("file_path", ""),
        )

    console = Console()
    console.print(table)
