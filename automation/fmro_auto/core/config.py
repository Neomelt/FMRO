"""Configuration management via pydantic-settings."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # FMRO backend
    fmro_api_base_url: str = "http://127.0.0.1:8080"
    fmro_api_timeout: float = 30.0

    # ADB
    adb_server_host: str = "127.0.0.1"
    adb_server_port: int = 5037
    adb_device_serial: str | None = None

    # Browser
    browser_headless: bool = True
    browser_slow_mo: int = 0

    # Scraping
    search_keywords: list[str] = ["机器人", "robotics"]
    scrape_max_pages: int = 3
    scrape_delay_seconds: float = 2.0

    # General
    log_level: str = "INFO"
    output_dir: str = "/app/output"
    screenshot_on_error: bool = True

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
