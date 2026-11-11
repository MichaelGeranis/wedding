"""Application configuration using pydantic-settings."""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = Field(..., description="Application environment")

    # API Configuration
    api_port: int = Field(default=8000, description="API server port")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL database URL")

    # CORS Configuration
    cors_origins: str = Field(..., description="Comma-separated list of allowed CORS origins")
    frontend_url: str = Field(..., description="Frontend application URL for QR codes")

    # Security
    jwt_secret_key: str = Field(..., description="Secret key for JWT token generation")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(default=60, description="JWT token expiration time in minutes")

    # Admin Configuration
    admin_password_hash: str = Field(..., description="Bcrypt hash of admin password")

    # Rate Limiting
    rate_limit_rsvp: str = Field(..., description="Rate limit for RSVP endpoint (max submissions per IP per day)")
    rate_limit_admin_login: str = Field(..., description="Rate limit for admin login endpoint")

    # RSVP Validation
    require_invited_guest_validation: bool = Field(default=False, description="Require phone number to be in invited guests list")

    # Email Configuration (all optional since email_enabled defaults to False)
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str | None = Field(default=None, description="SMTP username/email")
    smtp_password: str | None = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP connection")
    email_from_address: str | None = Field(default=None, description="From email address")
    email_from_name: str = Field(default="Wedding Planner", description="From name for emails")
    admin_email: str | None = Field(default=None, description="Admin email for notifications")
    email_enabled: bool = Field(default=False, description="Enable email notifications")

    @model_validator(mode="after")
    def _reject_demo_secret_outside_development(self) -> "Settings":
        """The demo JWT secret in docker/demo.env is public: never accept it outside development."""
        if self.environment != "development" and self.jwt_secret_key.startswith("demo-"):
            raise ValueError("JWT_SECRET_KEY is the public demo value; set your own secret outside development")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


# Global settings instance
settings = Settings()
