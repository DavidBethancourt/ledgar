"""Tests for the config module."""

import pytest

from ledgar.config import ALLOWED_CONFIG_KEYS, config_set, config_show, get_data_dir


class TestConfigSet:
    def test_set_valid_key(self, monkeypatch, tmp_path):
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("ledgar.config.DEFAULT_CONFIG_PATH", config_file)
        config_set("user-agent", "test/1.0")

    def test_set_invalid_key(self, monkeypatch, tmp_path):
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("ledgar.config.DEFAULT_CONFIG_PATH", config_file)
        with pytest.raises(ValueError, match="Unknown config key"):
            config_set("bad-key", "value")


class TestConfigShow:
    def test_defaults(self, monkeypatch, tmp_path):
        config_file = tmp_path / "nonexistent.toml"
        monkeypatch.setattr("ledgar.config.DEFAULT_CONFIG_PATH", config_file)
        result = config_show()
        assert "data-dir" in result
        assert "user-agent" in result

    def test_shows_set_values(self, monkeypatch, tmp_path):
        config_file = tmp_path / "config.toml"
        monkeypatch.setattr("ledgar.config.DEFAULT_CONFIG_PATH", config_file)
        config_set("user-agent", "test-agent/2.0")
        result = config_show()
        assert result["user-agent"] == "test-agent/2.0"


class TestGetDataDir:
    def test_cli_override(self, tmp_path):
        override = str(tmp_path / "custom-data")
        result = get_data_dir(override)
        assert result.exists()
        assert str(result) == override

    def test_default(self, monkeypatch, tmp_path):
        config_file = tmp_path / "nonexistent.toml"
        default_dir = tmp_path / "default-data"
        monkeypatch.setattr("ledgar.config.DEFAULT_CONFIG_PATH", config_file)
        monkeypatch.setattr("ledgar.config.DEFAULT_DATA_DIR", default_dir)
        result = get_data_dir()
        assert result == default_dir
