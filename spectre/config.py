from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: str = ""
    ws_host: str = "127.0.0.1"
    ws_port: int = 8765
    spectre_data_dir: Path = Path("./data/sessions")
    spectre_repo: str = "tmestery/SPECTRE"
    spectre_branch: str = "main"
    spectre_scope: str = "scopes/spectre.yaml"
    scope_dir: Path = Path("scopes")
    log_level: str = "INFO"


settings = Settings()
