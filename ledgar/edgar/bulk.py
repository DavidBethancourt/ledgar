"""Bulk download and extraction of companyfacts.zip."""

import json
import logging
import tempfile
import zipfile
from collections.abc import Iterator
from pathlib import Path

import click
from rich.progress import Progress

from ledgar.edgar.client import EdgarClient

log = logging.getLogger(__name__)

COMPANYFACTS_BULK_URL = (
    "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
)


def download_companyfacts_zip(client: EdgarClient, dest_dir: Path) -> Path:
    """Download companyfacts.zip with progress bar. Returns path to zip file."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "companyfacts.zip"

    click.echo("Downloading companyfacts.zip (~1.5 GB)...", err=True)
    resp = client.fetch_bytes(COMPANYFACTS_BULK_URL, stream=True)

    total = int(resp.headers.get("Content-Length", 0))
    with Progress() as progress:
        task = progress.add_task("Downloading...", total=total or None)
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                progress.update(task, advance=len(chunk))

    click.echo(f"Saved to {zip_path}", err=True)
    return zip_path


def iter_companyfacts(zip_path: Path) -> Iterator[tuple[int, dict]]:
    """Yield (cik, json_data) for each company in the companyfacts zip."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if n.endswith(".json")]
        click.echo(f"Extracting {len(names):,} company files...", err=True)

        with Progress() as progress:
            task = progress.add_task("Parsing...", total=len(names))
            for name in names:
                try:
                    data = json.loads(zf.read(name))
                    cik = data.get("cik")
                    if cik is not None:
                        yield int(cik), data
                except (json.JSONDecodeError, KeyError) as exc:
                    log.warning("Skipping %s: %s", name, exc)
                progress.update(task, advance=1)
