"""
CLI tool for checking if phone numbers are available.

Usage:
    python scripts/check_number.py
"""

from streamlit_app.utils.helpers import is_number_available, load_from_csv


def main():
    """Main function for checking phone number availability."""
    # Check if a number exists (using CSV - fast)
    test_number = "+915559876543"

    if is_number_available(test_number):
        print(f"✅ {test_number} is available!")
    else:
        print(f"❌ {test_number} not found")

    # Check with fresh API data (slower but up-to-date)
    print("\nChecking with fresh API data...")
    if is_number_available(test_number, refresh=True):
        print(f"✅ {test_number} is available!")
    else:
        print(f"❌ {test_number} not found")

    # Load all numbers and do custom checks
    all_numbers = load_from_csv()
    print(f"\nTotal available numbers: {len(all_numbers)}")

    # Find numbers by prefix
    mumbai_numbers = [n for n in all_numbers if n.startswith("+9122")]
    print(f"Mumbai numbers (+9122): {len(mumbai_numbers)}")

    delhi_numbers = [n for n in all_numbers if n.startswith("+9111")]
    print(f"Delhi numbers (+9111): {len(delhi_numbers)}")

    bangalore_numbers = [n for n in all_numbers if n.startswith("+9180")]
    print(f"Bangalore numbers (+9180): {len(bangalore_numbers)}")


if __name__ == "__main__":
    main()
