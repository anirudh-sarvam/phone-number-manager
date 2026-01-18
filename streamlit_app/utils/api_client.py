"""API client modules for phone number and endpoint management."""

import sys
from typing import Dict, List, Set, Union
import requests

from .config import config


class PhoneNumberAPI:
    """Client for phone number API operations."""

    @staticmethod
    def fetch_all_available_numbers(
        page_size: int = None, api_url: str = None, token: str = None
    ) -> Set[str]:
        """
        Fetch all available phone numbers from the API.

        Args:
            page_size: Number of items per page (default from config)
            api_url: Override API URL (for multi-org support)
            token: Override auth token (for multi-org support)

        Returns:
            Set of available phone numbers
        """
        if page_size is None:
            page_size = config.PAGE_SIZE

        # Use provided URL/token or fall back to config
        base_url = api_url if api_url else config.BASE_URL
        auth_token = token if token else config.SARVAM_TOKEN

        phone_numbers_url = f"{base_url}/phone-numbers?show_free_phone_numbers=true"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        offset = 0
        available = set()

        while True:
            url = f"{phone_numbers_url}&offset={offset}&limit={page_size}"

            try:
                response = requests.get(
                    url, headers=headers, timeout=config.API_TIMEOUT
                )

                if response.status_code == 401:
                    print(
                        "Error 401: Unauthorized - Check your SARVAM_TOKEN",
                        file=sys.stderr,
                    )
                    print(
                        "The authentication token may be expired or invalid.",
                        file=sys.stderr,
                    )
                    break

                if response.status_code == 404:
                    print("Error 404: Endpoint not found", file=sys.stderr)
                    print(f"Response: {response.text}", file=sys.stderr)
                    break

                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}", file=sys.stderr)
                break

            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            # Extract phone numbers from items
            for item in items:
                if isinstance(item, dict):
                    phone_num = item.get("phone_number") or item.get("number")
                    if phone_num:
                        available.add(phone_num)
                else:
                    available.add(str(item))

            offset += page_size

        return available


class EndpointAPI:
    """Client for endpoint API operations."""

    @staticmethod
    def create_endpoint(
        phone_numbers: Union[str, List[str]], verbose: bool = False
    ) -> Dict:
        """
        Create endpoints with the specified phone number(s).

        Args:
            phone_numbers: Single phone number or list of phone numbers
            verbose: Whether to print progress messages

        Returns:
            Response data from the API

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            requests.exceptions.RequestException: If the request fails
        """
        # Normalize input to list
        if isinstance(phone_numbers, str):
            phone_list = [phone_numbers]
        else:
            phone_list = phone_numbers

        headers = config.get_headers()
        payload = {"endpoints": phone_list}

        if verbose:
            print(f"Creating endpoint(s) for: {', '.join(phone_list)}")
            print(f"POST URL: {config.endpoints_url}")
            print(f"Payload: {payload}\n")

        try:
            response = requests.post(
                config.endpoints_url,
                json=payload,
                headers=headers,
                timeout=config.API_TIMEOUT,
            )

            if verbose:
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}\n")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e}"
            if hasattr(e, "response") and e.response is not None:
                error_msg += f"\nResponse: {e.response.text}"
            if verbose:
                print(error_msg, file=sys.stderr)
            raise
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"Request failed: {e}", file=sys.stderr)
            raise

    @staticmethod
    def create_single_endpoint(phone_number: str, verbose: bool = False) -> Dict:
        """
        Create a single endpoint (convenience wrapper).

        Args:
            phone_number: The phone number to register
            verbose: Whether to print progress messages

        Returns:
            Response data from the API
        """
        return EndpointAPI.create_endpoint(phone_number, verbose=verbose)

    @staticmethod
    def create_bulk_endpoints(phone_numbers: List[str], verbose: bool = False) -> Dict:
        """
        Create multiple endpoints in a single request.

        Args:
            phone_numbers: List of phone numbers to register
            verbose: Whether to print progress messages

        Returns:
            Response data from the API
        """
        return EndpointAPI.create_endpoint(phone_numbers, verbose=verbose)
