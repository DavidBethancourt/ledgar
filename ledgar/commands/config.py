"""Config CLI commands: set and show configuration."""

import click

from ledgar.config import ALLOWED_CONFIG_KEYS, config_set, config_show


@click.group()
def config():
    """Manage app configuration."""


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set_cmd(key: str, value: str):
    """Set a configuration value (e.g., user-agent, data-dir)."""
    try:
        config_set(key, value)
    except ValueError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"{key} = {value}")


@config.command("show")
def config_show_cmd():
    """Print current configuration."""
    cfg = config_show()
    for key, value in sorted(cfg.items()):
        display = value if value else "(not set)"
        click.echo(f"{key} = {display}")
