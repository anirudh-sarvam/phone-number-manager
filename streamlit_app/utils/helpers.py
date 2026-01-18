"""Helper functions for the Phone Number Manager application."""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Set

from .config import config
from .api_client import PhoneNumberAPI


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize a phone number by removing spaces, dashes, etc.

    Args:
        phone_number: The phone number to normalize

    Returns:
        Normalized phone number string
    """
    return phone_number.strip().replace(" ", "").replace("-", "")


def validate_phone_number(phone_number: str) -> bool:
    """
    Validate if a phone number has a valid format.

    Args:
        phone_number: The phone number to validate

    Returns:
        True if valid, False otherwise
    """
    # Basic validation: starts with + and has at least 10 digits
    normalized = normalize_phone_number(phone_number)
    pattern = r"^\+\d{10,15}$"
    return bool(re.match(pattern, normalized))


def format_timestamp(dt: datetime) -> str:
    """
    Format a datetime object for display.

    Args:
        dt: Datetime object to format

    Returns:
        Formatted datetime string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def save_to_csv(phone_numbers: Set[str], filename: str = None) -> None:
    """
    Save phone numbers to a CSV file.

    Args:
        phone_numbers: Set of phone numbers to save
        filename: CSV filename (uses config default if not provided)
    """
    if filename is None:
        filename = config.CSV_FILE

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["phone_number"])  # Header
        for number in sorted(phone_numbers):
            writer.writerow([number])
    print(f"Saved {len(phone_numbers)} numbers to {filename}")


def load_from_csv(filename: str = None) -> Set[str]:
    """
    Load phone numbers from CSV file.

    Args:
        filename: CSV filename (uses config default if not provided)

    Returns:
        Set of phone numbers
    """
    if filename is None:
        filename = config.CSV_FILE

    numbers: Set[str] = set()
    if not Path(filename).exists():
        return numbers

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "phone_number" in row and row["phone_number"]:
                numbers.add(row["phone_number"])
    return numbers


def is_number_available(
    phone_number: str, numbers_set: set = None, refresh: bool = False
) -> bool:
    """
    Check if a phone number is available.

    Args:
        phone_number: The phone number to check
        numbers_set: Set of phone numbers to check against (from session state)
        refresh: If True, fetch fresh data from API

    Returns:
        True if the number is available, False otherwise
    """
    if refresh:
        numbers = PhoneNumberAPI.fetch_all_available_numbers()
    elif numbers_set is not None:
        numbers = numbers_set
    else:
        # Fallback to empty set if no numbers provided
        numbers = set()

    # Normalize phone number
    normalized = normalize_phone_number(phone_number)

    # Check both normalized and original
    return normalized in numbers or phone_number in numbers
