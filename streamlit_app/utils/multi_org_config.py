"""Multi-organization configuration for the Phone Number Manager."""

import os
from typing import Dict, List
from pathlib import Path
import dotenv

# Import Streamlit only if available (for secrets support in cloud)
try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Load environment variables (for local development)
env_path = Path(__file__).parent.parent.parent / ".env"
dotenv.load_dotenv(dotenv_path=env_path, override=True)


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
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return value


# Organization and Provider Configuration
ORGS_CONFIG = {
    "Axis Bank": {
        "domain": "axisbank.com",
        "workspace": "axisbank-com-defau-3b9581",
        "token_key": "AXISBANK_TOKEN",
        "providers": [
            {
                "name": "Exotel - Sarvam Axon",
                "connection": "Sarvam-axon-cd6fd02e-42bf",
            }
        ],
    },
    "IDFC": {
        "domain": "idfc.com",
        "workspace": "idfc-com-default-9ed1f6",
        "token_key": "IDFC_TOKEN",
        "providers": [
            {
                "name": "Exotel - Sarvam 1M",
                "connection": "sarvam1m-cb138c90-e5a4",
            },
            {
                "name": "Exotel - Axonwise 1M",
                "connection": "axonwise1m-78a429af-1c86",
            },
        ],
    },
    "Mahindra Finance": {
        "domain": "mahindrafinance.com",
        "workspace": "mahindrafinance-co-b67665",
        "token_key": "MAHINDRAFINANCE_TOKEN",
        "providers": [
            {
                "name": "Exotel - Sarvam",
                "connection": "Exotel-Sarv-3c041e71-f2e9",
            },
            {
                "name": "Exotel - Axonwise 1M",
                "connection": "axonwise1m-d316de84-7340",
            },
            {
                "name": "Exotel - MMFSL",
                "connection": "MMFSL-Exote-2d992be6-54bf",
            },
        ],
    },
}


def get_org_list() -> List[str]:
    """Get list of available organizations."""
    return list(ORGS_CONFIG.keys())


def get_providers_for_org(org_name: str) -> List[Dict[str, str]]:
    """Get list of providers for a specific organization."""
    if org_name in ORGS_CONFIG:
        return ORGS_CONFIG[org_name]["providers"]
    return []


def build_api_url(org_name: str, provider_connection: str) -> str:
    """Build the API URL for a specific org and provider."""
    if org_name not in ORGS_CONFIG:
        return ""

    org = ORGS_CONFIG[org_name]
    base = "https://apps.sarvam.ai/api/app-authoring"
    url = (
        f"{base}/orgs/{org['domain']}/workspaces/{org['workspace']}/"
        f"channels/v2v/providers/exotel/connections/{provider_connection}"
    )
    return url


def get_token_for_org(org_name: str) -> str:
    """Get authentication token for a specific organization."""
    if org_name not in ORGS_CONFIG:
        return ""

    token_key = ORGS_CONFIG[org_name]["token_key"]
    return clean_env_value(token_key)


def get_org_info(org_name: str) -> Dict:
    """Get complete information for an organization."""
    if org_name not in ORGS_CONFIG:
        return {}
    return ORGS_CONFIG[org_name]
