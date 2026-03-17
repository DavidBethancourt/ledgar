"""Application configuration: paths, defaults, TOML read/write."""

import logging
from pathlib import Path

import tomli_w

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

log = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path.home() / ".ledgar" / "data"
DEFAULT_CONFIG_PATH = Path.home() / ".ledgar" / "config.toml"

ALLOWED_CONFIG_KEYS = {"user-agent", "data-dir"}


def _read_config_file() -> dict:
    """Read config.toml and return its contents as a dict."""
    if DEFAULT_CONFIG_PATH.exists():
        return tomllib.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _write_config_file(config: dict) -> None:
    """Write the config dict to config.toml."""
    DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_CONFIG_PATH.write_bytes(tomli_w.dumps(config).encode("utf-8"))


def config_set(key: str, value: str) -> None:
    """Set a configuration key to a value."""
    if key not in ALLOWED_CONFIG_KEYS:
        raise ValueError(
            f"Unknown config key '{key}'. Allowed keys: {', '.join(sorted(ALLOWED_CONFIG_KEYS))}"
        )
    config = _read_config_file()
    config[key] = value
    _write_config_file(config)
    log.info("Set %s = %s", key, value)


def config_show() -> dict:
    """Return the current configuration with defaults applied."""
    file_config = _read_config_file()
    return {
        "data-dir": file_config.get("data-dir", str(DEFAULT_DATA_DIR)),
        "user-agent": file_config.get("user-agent", ""),
    }


def get_data_dir(cli_override: str | None = None) -> Path:
    """Resolve the data directory. CLI flag > config file > default."""
    if cli_override:
        p = Path(cli_override)
    else:
        file_config = _read_config_file()
        p = Path(file_config.get("data-dir", str(DEFAULT_DATA_DIR)))
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_db_path(cli_data_dir: str | None = None) -> Path:
    """Return the path to the SQLite database file."""
    return get_data_dir(cli_data_dir) / "ledgar.db"


def get_user_agent() -> str:
    """Return the configured User-Agent string."""
    file_config = _read_config_file()
    ua = file_config.get("user-agent", "")
    if not ua:
        raise RuntimeError(
            "User-Agent not configured. SEC requires a User-Agent header.\n"
            "Run: ledgar config set user-agent \"YourApp/1.0 (your-email@example.com)\""
        )
    return ua
