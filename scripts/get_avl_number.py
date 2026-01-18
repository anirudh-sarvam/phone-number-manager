"""
CLI tool for fetching available phone numbers from the API.

Usage:
    python scripts/get_avl_number.py
"""

from streamlit_app.utils.api_client import PhoneNumberAPI
from streamlit_app.utils.helpers import save_to_csv
from streamlit_app.utils.config import config


def main():
    """Fetch numbers from API and save to CSV."""
    print("Fetching phone numbers from API...")
    print(f"Using CSV file: {config.CSV_FILE}\n")

    available_numbers = PhoneNumberAPI.fetch_all_available_numbers()
    print(f"Total numbers found: {len(available_numbers)}\n")

    # Save to CSV
    save_to_csv(available_numbers)

    # Display first 10 numbers as preview
    print("\nFirst 10 numbers:")
    for number in sorted(available_numbers)[:10]:
        print(f"  {number}")

    if len(available_numbers) > 10:
        print(f"... and {len(available_numbers) - 10} more")

    print(f"\n✅ Successfully saved to {config.CSV_FILE}")


if __name__ == "__main__":
    main()
