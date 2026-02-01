"""API client modules for phone number and endpoint management."""

import sys
from typing import Dict, List, Set, Union
import requests

from .config import config


class PhoneNumberAPI:
    """Client for phone number API operations."""

    @staticmethod
    def fetch_all_available_numbers(
        api_url: str = None, token: str = None, limit: int = 100
    ) -> Set[str]:
        """
        Fetch all available phone numbers from the API with pagination.

        Automatically paginates through all results until the end.

        Args:
            api_url: Full API URL (may already include /phone-numbers) or base URL
            token: Override auth token (for multi-org support)
            limit: Number of items per page (default: 100)

        Returns:
            Set of available phone numbers
        """
        # Use provided URL/token or fall back to config
        auth_token = token if token else config.SARVAM_TOKEN

        # If api_url is provided and already contains /phone-numbers, use it as-is
        # Otherwise, treat it as a base URL and append /phone-numbers
        if api_url:
            if "/phone-numbers" in api_url:
                # URL already includes /phone-numbers, use it directly
                phone_numbers_url = api_url
            else:
                # Treat as base URL and append /phone-numbers
                phone_numbers_url = f"{api_url}/phone-numbers"
        else:
            # Fall back to config
            phone_numbers_url = f"{config.BASE_URL}/phone-numbers"

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        available = set()
        offset = 0

        try:
            while True:
                # Build URL with pagination parameters
                separator = "&" if "?" in phone_numbers_url else "?"
                url = (
                    f"{phone_numbers_url}{separator}"
                    f"show_free_phone_numbers=true&offset={offset}&limit={limit}"
                )

                response = requests.get(
                    url, headers=headers, timeout=config.API_TIMEOUT
                )

                if response.status_code == 401:
                    break

                if response.status_code == 404:

                    # Try /endpoints as fallback (for providers like tata_tele)
                    # The /endpoints URL structure is different:
                    # /orgs/{org_id}/workspaces/{workspace_id}/connections/{connection_id}/endpoints
                    # vs /phone-numbers which uses:
                    # /orgs/{org_id}/workspaces/{workspace_id}/channels/v2v/providers/{provider}/connections/{connection_id}/phone-numbers

                    if "/channels/v2v/providers/" in phone_numbers_url:
                        # Extract base path: remove /channels/v2v/providers/{provider}/connections/{connection_id}/phone-numbers
                        # We need: /orgs/{org_id}/workspaces/{workspace_id}/connections/{connection_id}
                        parts = phone_numbers_url.split("/channels/v2v/providers/")
                        if len(parts) > 0:
                            base_path = parts[
                                0
                            ]  # This is: base_url/orgs/{org_id}/workspaces/{workspace_id}
                            # Extract connection_id from the original URL
                            connection_match = None
                            if "/connections/" in phone_numbers_url:
                                conn_part = phone_numbers_url.split("/connections/")[
                                    -1
                                ].split("/")[0]
                                if conn_part:
                                    endpoints_url = (
                                        f"{base_path}/connections/{conn_part}/endpoints"
                                    )

                                    try:
                                        endpoints_response = requests.get(
                                            f"{endpoints_url}?show_free_endpoints=false&offset={offset}&limit={limit}",
                                            headers=headers,
                                            timeout=config.API_TIMEOUT,
                                        )

                                        if endpoints_response.status_code == 200:
                                            endpoints_data = endpoints_response.json()

                                            # Parse endpoints response - endpoints might contain phone numbers
                                            if isinstance(endpoints_data, dict):
                                                endpoints_items = endpoints_data.get(
                                                    "items",
                                                    endpoints_data.get("data", []),
                                                )
                                                has_more = endpoints_data.get(
                                                    "has_more",
                                                    len(endpoints_items) == limit,
                                                )
                                            elif isinstance(endpoints_data, list):
                                                endpoints_items = endpoints_data
                                                has_more = len(endpoints_items) == limit
                                            else:
                                                endpoints_items = []
                                                has_more = False

                                            # Extract phone numbers from endpoints
                                            page_numbers_count = 0
                                            for endpoint in endpoints_items:
                                                if isinstance(endpoint, dict):
                                                    # Try various fields that might contain phone numbers
                                                    phone_num = (
                                                        endpoint.get("phone_number")
                                                        or endpoint.get("number")
                                                        or endpoint.get("phone")
                                                        or endpoint.get("endpoint")
                                                        or endpoint.get("id")
                                                    )
                                                    if phone_num:
                                                        available.add(str(phone_num))
                                                        page_numbers_count += 1
                                                elif isinstance(endpoint, str):
                                                    available.add(endpoint)
                                                    page_numbers_count += 1

                                            # If we got endpoints, continue pagination
                                            if (
                                                endpoints_items
                                                and has_more
                                                and len(endpoints_items) == limit
                                            ):
                                                offset += limit
                                                continue  # Continue pagination loop with /endpoints
                                            else:
                                                # No more endpoints, stop
                                                break
                                        else:
                                            break
                                    except Exception:
                                        break
                    break

                response.raise_for_status()

                data = response.json()

                # Handle different response formats
                if isinstance(data, dict):
                    items = data.get("items", [])
                    # Check if there are more pages
                    has_more = data.get("has_more", len(items) == limit)
                    total = data.get("total")
                    # Also check for other possible keys
                    if not items and "data" in data:
                        items = data.get("data", [])
                    if not items and "results" in data:
                        items = data.get("results", [])
                elif isinstance(data, list):
                    items = data
                    has_more = len(items) == limit
                    total = None
                else:
                    items = []
                    has_more = False
                    total = None

                # Extract phone numbers from items
                page_numbers_count = 0
                for item in items:
                    if isinstance(item, dict):
                        # Try multiple possible field names for phone number
                        phone_num = (
                            item.get("phone_number")
                            or item.get("number")
                            or item.get("phone")
                            or item.get("endpoint")
                            or item.get("id")  # Sometimes ID is the phone number
                        )
                        if phone_num:
                            available.add(str(phone_num))
                            page_numbers_count += 1
                    elif isinstance(item, str):
                        # Item is already a phone number string
                        available.add(item)
                        page_numbers_count += 1
                    else:
                        # Try to convert to string
                        available.add(str(item))
                        page_numbers_count += 1

                # Check if we've reached the end
                if not items or len(items) < limit or not has_more:
                    break

                offset += limit

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}", file=sys.stderr)

        return available


class EndpointAPI:
    """Client for endpoint API operations."""

    @staticmethod
    def create_endpoint(
        phone_numbers: Union[str, List[str]],
        base_url: str = None,
        token: str = None,
        verbose: bool = False,
    ) -> Dict:
        """
        Create endpoints with the specified phone number(s).

        Args:
            phone_numbers: Single phone number or list of phone numbers
            base_url: Optional API base URL (from session state)
            token: Optional API token (from session state)
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

        # Use provided base_url and token, or fall back to config
        if base_url and token:
            endpoints_url = f"{base_url}/endpoints"
            headers = {"Authorization": f"Bearer {token}"}
        else:
            endpoints_url = config.endpoints_url
            headers = config.get_headers()

        # API expects endpoints as list of phone number strings
        payload = {"endpoints": phone_list}

        if verbose:
            print(f"Creating endpoint(s) for: {', '.join(phone_list)}")
            print(f"POST URL: {endpoints_url}")
            print(f"Payload: {payload}\n")

        try:
            response = requests.post(
                endpoints_url,
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
            error_msg = f"{e}"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f"\nAPI Error Details: {error_details}"
                except:
                    error_msg += f"\nResponse Text: {e.response.text}"
            if verbose:
                print(error_msg, file=sys.stderr)
            raise ValueError(error_msg) from e
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"Request failed: {e}", file=sys.stderr)
            raise

    @staticmethod
    def create_single_endpoint(
        phone_number: str,
        base_url: str = None,
        token: str = None,
        verbose: bool = False,
    ) -> Dict:
        """
        Create a single endpoint (convenience wrapper).

        Args:
            phone_number: The phone number to register
            base_url: Optional API base URL (from session state)
            token: Optional API token (from session state)
            verbose: Whether to print progress messages

        Returns:
            Response data from the API
        """
        return EndpointAPI.create_endpoint(
            phone_number, base_url=base_url, token=token, verbose=verbose
        )

    @staticmethod
    def create_bulk_endpoints(
        phone_numbers: List[str],
        base_url: str = None,
        token: str = None,
        verbose: bool = False,
    ) -> Dict:
        """
        Create multiple endpoints in a single request.

        Args:
            phone_numbers: List of phone numbers to register
            base_url: Optional API base URL (from session state)
            token: Optional API token (from session state)
            verbose: Whether to print progress messages

        Returns:
            Response data from the API
        """
        return EndpointAPI.create_endpoint(
            phone_numbers, base_url=base_url, token=token, verbose=verbose
        )
