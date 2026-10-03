from functools import lru_cache
from typing import Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres"
    auth_provider: Literal["supabase", "development"] = "supabase"
    storage_provider: Literal["supabase", "local"] = "supabase"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    dev_token_secret: str = ""
    private_storage_dir: str = ".local/private"
    api_base_url: str = "http://127.0.0.1:8000"
    web_base_url: str = "http://127.0.0.1:8081"
    cors_origins: str = "http://localhost:8081,http://127.0.0.1:8081"
    ollama_base_url: str = "http://127.0.0.1:11434"
    chat_provider: Literal["ollama", "extractive", "openai_compatible"] = "ollama"
    embedding_provider: Literal["ollama", "development"] = "ollama"
    chat_model: str = "qwen2.5:1.5b"
    embedding_model: str = "nomic-embed-text"
    model_api_url: str = ""
    model_api_key: str = ""
    pos_connector: Literal["csv", "odoo", "development"] = "csv"
    odoo_base_url: str = ""
    odoo_database: str = ""
    odoo_api_key: str = ""
    odoo_username: str = ""
    odoo_mapping_file: str = ""
    odoo_api_verified: bool = False
    support_owner_email: str = ""
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "support@nicecomp.test"
    smtp_starttls: bool = True
    email_provider: Literal["mailpit", "smtp"] = "mailpit"
    production_recipient_confirmed: bool = False

    @model_validator(mode="after")
    def protect_modes(self):
        if self.auth_provider == "development" and len(self.dev_token_secret) < 32:
            raise ValueError(
                "Development auth requires a random DEV_TOKEN_SECRET of at least 32 characters"
            )
        if self.email_provider == "mailpit" and self.smtp_host not in (
            "localhost",
            "127.0.0.1",
            "mailpit",
        ):
            raise ValueError("Mailpit must use the local capture service")
        if self.app_env != "production" and self.email_provider != "mailpit":
            raise ValueError("Development/test email must use Mailpit")
        if self.app_env == "production":
            if (
                self.auth_provider != "supabase"
                or self.storage_provider != "supabase"
                or not self.database_url.startswith("postgresql")
                or self.pos_connector == "development"
                or self.embedding_provider == "development"
                or self.chat_provider == "extractive"
            ):
                raise ValueError("Development providers cannot run in production")
            if (
                not self.production_recipient_confirmed
                or not self.support_owner_email
                or self.email_provider != "smtp"
            ):
                raise ValueError("Production email recipient must be confirmed")
            if not self.smtp_starttls or not self.api_base_url.startswith("https://"):
                raise ValueError("Production requires HTTPS and SMTP STARTTLS")
        return self


@lru_cache
def settings():
    return Settings()
