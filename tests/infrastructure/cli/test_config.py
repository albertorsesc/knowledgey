import pytest
from typer.testing import CliRunner

from knowledgey.infrastructure.cli.app import app
from knowledgey.infrastructure.config import get_settings

runner = CliRunner()


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()


def test_data_dir_defaults_under_home() -> None:
    assert get_settings().data_dir.name == ".knowledgey"


def test_env_var_overrides_data_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KG_DATA_DIR", "/tmp/kg-test")
    get_settings.cache_clear()
    assert str(get_settings().data_dir) == "/tmp/kg-test"


def test_settings_are_cached() -> None:
    assert get_settings() is get_settings()


def test_config_command_runs_without_env_file() -> None:
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "data_dir" in result.output
