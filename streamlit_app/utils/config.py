"""Configuration module for the Phone Number Manager application."""

import os
from dataclasses import dataclass
from pathlib import Path
import dotenv

# Import Streamlit only if available (for secrets support in cloud)
try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Force load .env from project root (for local development)
env_path = Path(__file__).parent.parent.parent / ".env"
dotenv.load_dotenv(dotenv_path=env_path, override=True)


# Get values and aggressively strip quotes and whitespace
def clean_env_value(key: str) -> str:
    """Get environment variable and clean it of quotes and whitespace.

    Supports both .env files (local) and Streamlit secrets (cloud).
    """
    # Try Streamlit secrets first (for cloud deployment)
    if HAS_STREAMLIT:
        try:
            if hasattr(st, "secrets") and key in st.secrets:
                value = st.secrets[key]
                if isinstance(value, str):
                    value = value.strip()
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]
                    return value
        except Exception:
            pass

    # Fall back to environment variables (for local development)
    value = os.getenv(key) or ""
    # Strip whitespace
    value = value.strip()
    # Remove surrounding quotes (both single and double)
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return value


BASE_URL = clean_env_value("BASE_URL")
SARVAM_TOKEN = clean_env_value("SARVAM_TOKEN")


@dataclass
class AppConfig:
    """Application configuration class."""

    # API Configuration
    SARVAM_TOKEN: str = SARVAM_TOKEN

    # Base URLs
    BASE_URL: str = BASE_URL

    @property
    def phone_numbers_url(self) -> str:
        """Get the phone numbers API URL."""
        return f"{self.BASE_URL}/phone-numbers?show_free_phone_numbers=true"

    @property
    def endpoints_url(self) -> str:
        """Get the endpoints API URL."""
        return f"{self.BASE_URL}/endpoints"

    # File Configuration
    CSV_FILE: str = "available_phone_numbers.csv"

    # API Configuration
    API_TIMEOUT: int = 30
    PAGE_SIZE: int = 50

    # Streamlit Configuration
    PAGE_TITLE: str = "Phone Number Manager"
    PAGE_ICON: str = "📞"
    LAYOUT: str = "wide"

    def get_headers(self) -> dict:
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.SARVAM_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


# Global config instance
config = AppConfig()
