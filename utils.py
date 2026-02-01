"""Utility functions for fetching organizational data from Sarvam API.

This module provides functions to auto-fetch workspaces, providers, connections,
and phone numbers using admin credentials from secrets.toml.
"""

import requests
import streamlit as st
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_base_url(env: str) -> str:
    """Get base URL for the specified environment."""
    return st.secrets[env]["url"]


def login(env: str) -> str:
    """Login and get authentication token using admin credentials from secrets.toml.

    Args:
        env: Environment name (prod, staging, qa)

    Returns:
        Authentication token string

    Raises:
        requests.exceptions.HTTPError: If login fails
    """
    base_url = get_base_url(env)
    user_id = st.secrets[env]["user_id"]
    password = st.secrets[env]["password"]
    org_id = st.secrets[env]["org_id"]
    path = "/api/auth/login"
    full_url = f"{base_url}{path}"
    payload = {"user_id": user_id, "password": password, "org_id": org_id}

    logger.info(f"Attempting login to {full_url} for org_id: {org_id}")
    try:
        response = requests.post(full_url, json=payload)
        response.raise_for_status()
        logger.info(f"Login successful for org_id: {org_id}")
        return response.json()["access_token"]
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTPError during login for org_id: {org_id}. "
            f"Status: {e.response.status_code}, Response: {e.response.text}"
        )
        raise


def get_orgs(env: str, token: str) -> list[dict]:
    """Fetch all organizations accessible with the given token.

    Args:
        env: Environment name (prod, staging, qa)
        token: Authentication token

    Returns:
        List of organization dictionaries

    Raises:
        requests.exceptions.HTTPError: If API request fails
    """
    base_url = get_base_url(env)
    path = "/api/org/orgs"
    full_url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    logger.info(f"Fetching all organizations from {full_url}")
    try:
        response = requests.get(full_url, headers=headers)
        response.raise_for_status()
        orgs = response.json()
        logger.info(f"Successfully fetched {len(orgs)} organizations")
        return orgs
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTPError fetching organizations: {e.response.status_code}, {e.response.text}"
        )
        raise


def get_workspaces(env: str, token: str, org_id: str) -> list[dict]:
    """Fetch all workspaces for a given organization.

    Args:
        env: Environment name (prod, staging, qa)
        token: Authentication token
        org_id: Organization ID

    Returns:
        List of workspace dictionaries

    Raises:
        requests.exceptions.HTTPError: If API request fails
    """
    base_url = get_base_url(env)
    path = f"/api/org/orgs/{org_id}/workspaces"
    full_url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    logger.info(f"Fetching workspaces for org {org_id} from {full_url}")
    response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    result = response.json()

    # Handle different response formats
    if isinstance(result, dict):
        # If response is a dict, check for 'items' key (paginated response)
        if "items" in result:
            workspaces = result["items"]
        else:
            # If it's a dict but not paginated, wrap it in a list
            workspaces = [result] if result else []
    elif isinstance(result, list):
        workspaces = result
    else:
        # Unexpected format, return empty list
        logger.warning(f"Unexpected workspaces response format: {type(result)}")
        workspaces = []

    logger.info(f"Successfully fetched {len(workspaces)} workspaces for org {org_id}")
    return workspaces


def get_connections_from_workspace(
    env: str, token: str, org_id: str, workspace_id: str
) -> list[dict]:
    """Fetch all connections for a given workspace.

    Args:
        env: Environment name (prod, staging, qa)
        token: Authentication token
        org_id: Organization ID
        workspace_id: Workspace ID

    Returns:
        List of connection dictionaries

    Raises:
        requests.exceptions.HTTPError: If API request fails
    """
    base_url = get_base_url(env)
    path = f"/api/app-authoring/orgs/{org_id}/workspaces/{workspace_id}/connections"
    full_url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    logger.info(f"Fetching connections for workspace {workspace_id} from {full_url}")
    try:
        response = requests.get(full_url, headers=headers)
        response.raise_for_status()
        result = response.json()

        # Handle different response formats
        if isinstance(result, dict):
            # If response is a dict, check for 'items' key (paginated response)
            if "items" in result:
                connections_raw = result["items"]
            else:
                # If it's a dict but not paginated, wrap it in a list
                connections_raw = [result] if result else []
        elif isinstance(result, list):
            connections_raw = result
        else:
            # Unexpected format, return empty list
            logger.warning(f"Unexpected connections response format: {type(result)}")
            connections_raw = []

        # Convert string connection IDs to dict format if needed
        connections = []
        for conn in connections_raw:
            if isinstance(conn, str):
                # API returned connection ID as string, convert to dict
                # Skip empty strings
                if conn and conn.strip():
                    connections.append({"id": conn, "name": conn})
                else:
                    logger.warning(f"Skipping empty connection string")
            elif isinstance(conn, dict):
                # Try to get id from various possible fields
                conn_id = (
                    conn.get("id")
                    or conn.get("connection_id")
                    or conn.get("connectionId")
                )
                if conn_id and str(conn_id).strip():
                    # Preserve all original fields and ensure id is set
                    normalized_conn = conn.copy()
                    normalized_conn["id"] = str(conn_id).strip()  # Ensure id is set
                    if "name" not in normalized_conn or not normalized_conn["name"]:
                        normalized_conn["name"] = str(conn_id).strip()
                    connections.append(normalized_conn)
                else:
                    logger.warning(f"Skipping connection dict without valid id: {conn}")
            else:
                logger.warning(f"Skipping invalid connection format: {type(conn)}")

        logger.info(
            f"Successfully fetched {len(connections)} connections for workspace {workspace_id}"
        )
        return connections
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTPError fetching connections: {e.response.status_code}, {e.response.text}"
        )
        raise


def get_phone_numbers(
    env: str,
    token: str,
    org_id: str,
    workspace_id: str,
    connection_id: str,
    provider: str = "exotel",
    show_free_phone_numbers: bool = True,
    limit: int = 100,
) -> list[dict]:
    """Fetch all phone numbers for a given connection with pagination.

    Automatically paginates through all results until the end.

    Args:
        env: Environment name (prod, staging, qa)
        token: Authentication token
        org_id: Organization ID
        workspace_id: Workspace ID
        connection_id: Connection ID
        provider: Provider name (default: "exotel")
        show_free_phone_numbers: Whether to show free phone numbers (default: True)
        limit: Number of items per page (default: 100)

    Returns:
        List of phone number dictionaries (all pages combined)

    Raises:
        requests.exceptions.HTTPError: If API request fails
    """
    base_url = get_base_url(env)
    path = (
        f"/api/app-authoring/orgs/{org_id}/workspaces/{workspace_id}/"
        f"channels/v2v/providers/{provider}/connections/{connection_id}/phone-numbers"
    )
    full_url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    logger.info(
        f"Fetching phone numbers for connection {connection_id} from {full_url}"
    )

    all_phone_numbers = []
    offset = 0

    try:
        while True:
            params = {
                "show_free_phone_numbers": str(show_free_phone_numbers).lower(),
                "offset": offset,
                "limit": limit,
            }

            response = requests.get(full_url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            # Handle paginated response
            if isinstance(result, dict):
                if "items" in result:
                    page_items = result["items"]
                    # Check if there are more pages
                    total = result.get("total", len(page_items))
                    has_more = result.get("has_more", len(page_items) == limit)
                else:
                    # Single dict response, treat as one item
                    page_items = [result] if result else []
                    has_more = False
            elif isinstance(result, list):
                page_items = result
                has_more = len(page_items) == limit
            else:
                page_items = []
                has_more = False

            if not page_items:
                # No more items, stop pagination
                break

            all_phone_numbers.extend(page_items)
            logger.info(
                f"Fetched page {offset // limit + 1}: {len(page_items)} phone numbers "
                f"(total so far: {len(all_phone_numbers)})"
            )

            # Check if we've reached the end
            if len(page_items) < limit or not has_more:
                break

            offset += limit

        logger.info(
            f"Successfully fetched {len(all_phone_numbers)} total phone numbers "
            f"for connection {connection_id}"
        )
        return all_phone_numbers
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTPError fetching phone numbers: {e.response.status_code}, {e.response.text}"
        )
        raise


def auto_fetch_org_data(org_id: str = None, env: str = "prod") -> dict:
    """Auto-fetch all organizational data including workspaces, connections, and phone numbers.

    This function uses admin credentials from secrets.toml to fetch all organizational data.
    The API structure is: org -> workspaces -> connections -> phone numbers

    Args:
        org_id: Organization ID (if None, uses org_id from secrets.toml)
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        Dictionary containing:
        {
            "org_id": str,
            "workspaces": list[dict],
            "connections": dict[workspace_id: list[dict]],
            "phone_numbers": dict[connection_id: list[dict]],
            "token": str
        }
    """
    logger.info(f"Starting auto-fetch for org data in {env} environment")

    # Login with admin credentials from secrets.toml
    token = login(env)
    if org_id is None:
        org_id = st.secrets[env]["org_id"]

    # Fetch workspaces
    logger.info(f"Fetching workspaces for org {org_id}")
    workspaces = get_workspaces(env, token, org_id)

    # Fetch connections for each workspace
    connections_by_workspace = {}
    phone_numbers_by_connection = {}

    for workspace in workspaces:
        workspace_id = workspace.get("id") or workspace.get("workspace_id")
        workspace_name = workspace.get("name", workspace_id)
        logger.info(
            f"Fetching connections for workspace {workspace_name} ({workspace_id})"
        )

        try:
            connections = get_connections_from_workspace(
                env, token, org_id, workspace_id
            )
            connections_by_workspace[workspace_id] = connections

            # Fetch phone numbers for each connection
            for connection in connections:
                # Handle both dict and string formats
                if isinstance(connection, dict):
                    connection_id = connection.get("id")
                    connection_name = connection.get("name", connection_id)
                elif isinstance(connection, str):
                    connection_id = connection
                    connection_name = connection_id
                else:
                    logger.warning(
                        f"Skipping invalid connection format: {type(connection)}"
                    )
                    continue

                logger.info(
                    f"Fetching phone numbers for connection {connection_name} ({connection_id})"
                )

                try:
                    phone_numbers = get_phone_numbers(
                        env, token, org_id, workspace_id, connection_id
                    )
                    phone_numbers_by_connection[connection_id] = phone_numbers
                except Exception as e:
                    logger.error(
                        f"Failed to fetch phone numbers for connection {connection_id}: {e}"
                    )
                    phone_numbers_by_connection[connection_id] = []

        except Exception as e:
            logger.error(
                f"Failed to fetch connections for workspace {workspace_id}: {e}"
            )
            connections_by_workspace[workspace_id] = []

    result = {
        "org_id": org_id,
        "workspaces": workspaces,
        "connections": connections_by_workspace,
        "phone_numbers": phone_numbers_by_connection,
        "token": token,  # Include token for future API calls
    }

    total_connections = sum(len(c) for c in connections_by_workspace.values())
    total_numbers = sum(len(p) for p in phone_numbers_by_connection.values())

    logger.info(
        f"Auto-fetch completed: {len(workspaces)} workspaces, "
        f"{total_connections} total connections, {total_numbers} total phone numbers"
    )

    return result


def get_all_phone_numbers_flat(org_id: str = None, env: str = "prod") -> list[dict]:
    """Fetch all phone numbers from all workspaces and connections in a flat list.

    Each phone number dictionary is enriched with workspace and connection information.

    Args:
        org_id: Organization ID (if None, uses org_id from secrets.toml)
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        List of phone number dictionaries with added fields:
        - workspace_id: Workspace ID
        - workspace_name: Workspace name
        - connection_id: Connection ID
        - connection_name: Connection name
    """
    data = auto_fetch_org_data(org_id, env)

    all_numbers = []
    for workspace in data["workspaces"]:
        workspace_id = workspace.get("id") or workspace.get("workspace_id")
        workspace_name = workspace.get("name", workspace_id)

        connections = data["connections"].get(workspace_id, [])
        for connection in connections:
            connection_id = connection.get("id")
            connection_name = connection.get("name", connection_id)

            phone_numbers = data["phone_numbers"].get(connection_id, [])
            for phone_number in phone_numbers:
                # Enrich phone number with workspace and connection info
                enriched_number = phone_number.copy()
                enriched_number["workspace_id"] = workspace_id
                enriched_number["workspace_name"] = workspace_name
                enriched_number["connection_id"] = connection_id
                enriched_number["connection_name"] = connection_name
                all_numbers.append(enriched_number)

    logger.info(
        f"Collected {len(all_numbers)} phone numbers across all workspaces and connections"
    )
    return all_numbers
