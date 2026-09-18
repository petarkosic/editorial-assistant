from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """`database_url` / `env` / `openai_api_key` are required - no in-code
    fallback. Missing one crashes on startup with a clear pydantic error
    instead of silently running against the wrong DB or without a real key.
    `allowed_origins` is low-risk (not a secret, failure is a loud CORS error
    in the browser) so it keeps a sane local-dev default.

    All values come from real env vars or `.env` - see `.env.example`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    env: str
    openai_api_key: str
    allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
