"""Configuration module for the Phone Number Manager application.

Uses secrets.toml for configuration (not .env).
"""

from dataclasses import dataclass

# Import Streamlit only if available (for secrets support)
try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def _get_secret_value(key: str, default: str = "") -> str:
    """Get value from Streamlit secrets.

    Args:
        key: Secret key (supports nested keys like "api.base_url")
        default: Default value if key not found

    Returns:
        Secret value as string
    """
    if not HAS_STREAMLIT:
        return default

    try:
        if hasattr(st, "secrets"):
            # Handle nested keys like "api.base_url"
            keys = key.split(".")
            value = st.secrets
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
                if value is None:
                    return default

            if isinstance(value, str):
                value = value.strip()
                # Remove surrounding quotes
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
            return str(value) if value is not None else default
    except Exception:
        pass

    return default


# Get configuration from secrets.toml
BASE_URL = _get_secret_value("api.base_url", "")
SARVAM_TOKEN = _get_secret_value("api.token", "")


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
