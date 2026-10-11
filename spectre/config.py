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
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = ""
    llm_timeout_seconds: float = 60.0
    llm_enabled: bool = True
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    agent_reasoning_max_steps: int = 6
    judges_enabled: bool = True
    handoff_profile: str = "default"
    handoff_profiles_dir: Path = Path("handoff_profiles")

    @property
    def llm_api_key(self) -> str:
        if self.llm_provider == "groq":
            return self.groq_api_key
        if self.llm_provider == "openai":
            return self.openai_api_key
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return ""

    @property
    def llm_base_url_resolved(self) -> str:
        if self.llm_base_url:
            return self.llm_base_url
        if self.llm_provider == "groq":
            return "https://api.groq.com/openai/v1"
        if self.llm_provider == "openai":
            return "https://api.openai.com/v1"
        if self.llm_provider == "ollama":
            return "http://localhost:11434/v1"
        return "https://api.groq.com/openai/v1"


settings = Settings()
