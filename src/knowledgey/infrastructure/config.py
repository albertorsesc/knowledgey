from functools import cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KG_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".knowledgey",
        description="Directory where ingested documents and local state are stored.",
    )

    def as_dict(self) -> dict[str, str]:
        return {"data_dir": str(self.data_dir)}


@cache
def get_settings() -> Settings:
    return Settings()
