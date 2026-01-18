"""
CLI tool for creating endpoints with phone numbers.

Usage:
    python scripts/add_to_org.py <phone_number> [phone_number2 ...]
    python scripts/add_to_org.py +915551234567
    python scripts/add_to_org.py +915551234567 +915551234568
"""

import sys
import requests

from streamlit_app.utils.api_client import EndpointAPI


def main():
    """CLI entry point for creating endpoints."""
    if len(sys.argv) > 1:
        phone_numbers = sys.argv[1:]
    else:
        # Default phone number - CHANGE THIS to a number not yet registered
        phone_numbers = ["+915551234567"]
        print(f"No phone number provided. Using default: {phone_numbers[0]}")
        print("\nUsage:")
        print("  python scripts/add_to_org.py <phone_number> [phone_number2 ...]")
        print("\nExamples:")
        print("  python scripts/add_to_org.py +915551234567")
        print("  python scripts/add_to_org.py +915551234567 +915551234568\n")

    try:
        result = EndpointAPI.create_endpoint(phone_numbers, verbose=True)
        print("\n" + "=" * 70)
        print("✅ SUCCESS: Endpoint(s) created successfully!")
        print("=" * 70)
        print(f"Result: {result}")
        return result
    except requests.exceptions.HTTPError as e:
        error_text = str(e)
        if hasattr(e, "response") and e.response is not None:
            error_text += f" {e.response.text}"

        if "already exist" in error_text.lower():
            print(
                f"\n⚠️  WARNING: One or more phone numbers already exist "
                "as endpoints!"
            )
            print("Please choose different phone number(s).")
        else:
            print(f"\n❌ FAILED: Could not create endpoint: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FAILED: Could not create endpoint: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
