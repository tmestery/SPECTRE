from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: str = ""
    ws_port: int = 8765
    spectre_data_dir: Path = Path("./data/sessions")
    log_level: str = "INFO"


settings = Settings()
