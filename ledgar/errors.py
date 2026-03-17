"""Exception hierarchy for Ledgar."""


class LedgarError(Exception):
    """Base exception for all Ledgar errors."""


class DataStoreError(LedgarError):
    """Error accessing or operating on the local data store."""


class EdgarClientError(LedgarError):
    """Error communicating with SEC EDGAR."""


class ConfigError(LedgarError):
    """Error reading or writing configuration."""
