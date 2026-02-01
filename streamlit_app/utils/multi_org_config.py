"""Multi-organization configuration for the Phone Number Manager.

This module dynamically fetches organizations, providers, and connections
from the Sarvam API using admin credentials from secrets.toml.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)

# Add parent directory to path to import utils.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import utils  # noqa: E402


def _get_admin_token(env: str = "prod") -> str:
    """Get admin authentication token using credentials from secrets.toml.

    Caches token in session state to avoid repeated logins.
    """
    cache_key = f"admin_token_{env}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = utils.login(env)
    return st.session_state[cache_key]


def _get_orgs_data(env: str = "prod") -> List[Dict]:
    """Fetch all organizations and cache in session state.

    Returns:
        List of organization dictionaries with id, name, domain, etc.
    """
    cache_key = f"orgs_data_{env}"
    if cache_key not in st.session_state:
        token = _get_admin_token(env)
        st.session_state[cache_key] = utils.get_orgs(env, token)
    return st.session_state[cache_key]


def _normalize_connections(connections: list) -> list:
    """Normalize connections to dict format.

    Converts string connection IDs to dict format: {"id": conn_id, "name": conn_id}
    Filters out empty or invalid connections.

    Args:
        connections: List of connections (can be strings or dicts)

    Returns:
        List of connection dicts with valid "id" fields
    """
    normalized = []
    for conn in connections:
        if isinstance(conn, str):
            # Convert string to dict, but skip empty strings
            if conn and conn.strip():
                normalized.append({"id": conn, "name": conn})
            else:
                logger.warning(f"Skipping empty connection string")
        elif isinstance(conn, dict):
            # Try to get id from various possible fields
            conn_id = (
                conn.get("id")
                or conn.get("connection_id")
                or conn.get("connectionId")
                or conn.get("name")  # Fallback to name if id is missing
            )

            if conn_id and str(conn_id).strip():
                # Ensure both id and name are set
                # Preserve all original fields (including channel_provider)
                normalized_conn = conn.copy()
                normalized_conn["id"] = str(conn_id).strip()  # Ensure id is set
                if "name" not in normalized_conn or not normalized_conn["name"]:
                    normalized_conn["name"] = str(conn_id).strip()
                # Ensure channel_provider is preserved (important for building URLs)
                if "channel_provider" not in normalized_conn:
                    # Try to infer from other fields if missing
                    normalized_conn["channel_provider"] = (
                        normalized_conn.get("provider") or "exotel"
                    )
                normalized.append(normalized_conn)
            else:
                logger.warning(f"Skipping connection dict without valid id: {conn}")
        else:
            logger.warning(f"Skipping invalid connection format: {type(conn)}")
    return normalized


def _get_org_full_data(org_id: str, env: str = "prod") -> Dict:
    """Fetch full data for an organization.

    Fetches workspaces and connections from each workspace.
    Caches data in session state.

    Returns:
        Dictionary with keys: workspaces, connections (by workspace_id)
    """
    cache_key = f"org_full_data_{org_id}_{env}"
    if cache_key not in st.session_state:
        token = _get_admin_token(env)
        workspaces = utils.get_workspaces(env, token, org_id)

        # Fetch connections for each workspace
        connections_by_workspace = {}
        for workspace in workspaces:
            # Ensure workspace is a dict, not a string
            if not isinstance(workspace, dict):
                logger.warning(f"Skipping invalid workspace format: {type(workspace)}")
                continue

            workspace_id = workspace.get("id") or workspace.get("workspace_id")
            if workspace_id:
                try:
                    connections = utils.get_connections_from_workspace(
                        env, token, org_id, workspace_id
                    )
                    # Normalize connections to ensure they're in dict format
                    connections_by_workspace[workspace_id] = _normalize_connections(
                        connections
                    )
                except Exception as e:
                    # If connections endpoint returns 404, workspace may not have connections
                    if "404" in str(e) or "Not Found" in str(e):
                        # Workspace may not have connections configured
                        connections_by_workspace[workspace_id] = []
                    else:
                        error_msg = (
                            f"Failed to fetch connections "
                            f"for workspace {workspace_id}: {e}"
                        )
                        st.error(error_msg)
                        connections_by_workspace[workspace_id] = []

        st.session_state[cache_key] = {
            "workspaces": workspaces,
            "connections": connections_by_workspace,
        }
    else:
        # Normalize cached connections in case they're still strings
        cached_data = st.session_state[cache_key]
        connections_by_workspace = cached_data.get("connections", {})
        for workspace_id, connections in connections_by_workspace.items():
            cached_data["connections"][workspace_id] = _normalize_connections(
                connections
            )

    return st.session_state[cache_key]


def get_org_list(env: str = "prod") -> List[str]:
    """Get list of all available organization names.

    Args:
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        List of organization names (sorted alphabetically)
    """
    try:
        orgs = _get_orgs_data(env)
        # Extract organization names - prefer name, then domain, then id
        org_names = []
        for org in orgs:
            # Prefer display name, fallback to domain, then id
            name = (
                org.get("name")
                or org.get("display_name")
                or org.get("domain")
                or org.get("id")
                or org.get("org_id")
                or org.get("orgId")
            )
            if name:
                org_names.append(str(name))
        return sorted(org_names)
    except Exception as e:
        st.error(f"Failed to fetch organizations: {e}")
        return []


def get_org_id_by_name(org_name: str, env: str = "prod") -> Optional[str]:
    """Get organization ID by organization name.

    Args:
        org_name: Organization name (can be name, id, or domain)
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        Organization ID or None if not found
    """
    orgs = _get_orgs_data(env)
    search_name = org_name.lower().strip()

    if not orgs:
        st.warning("No organizations found in API response")
        return None

    for org in orgs:
        # Get all possible identifier fields (case-insensitive for matching)
        org_name_field = str(org.get("name", "")).lower().strip()
        org_display_name = str(org.get("display_name", "")).lower().strip()
        org_domain = str(org.get("domain", "")).lower().strip()
        org_org_domain = str(org.get("org_domain", "")).lower().strip()
        org_id_field = str(org.get("id", "")).lower().strip()
        # Keep original case for org_id
        org_org_id_raw = org.get("org_id")
        org_org_id = str(org_org_id_raw or "").lower().strip()
        org_orgId = str(org.get("orgId", "")).lower().strip()

        # Get the actual org_id (for API calls) - use ORIGINAL case
        # Priority: org_id > orgId > extract from domain
        actual_org_id = None
        if org_org_id_raw:
            actual_org_id = org_org_id_raw  # Keep original case
        elif org.get("orgId"):
            actual_org_id = org.get("orgId")  # Keep original case

        # Check if this org matches the search name
        matches = False
        matched_field = None

        # Exact matches first (most reliable)
        if (
            org_name_field == search_name
            or org_display_name == search_name
            or org_domain == search_name
            or org_org_domain == search_name
            or org_id_field == search_name
            or org_org_id == search_name
            or org_orgId == search_name
        ):
            matches = True
            if org_domain == search_name or org_org_domain == search_name:
                matched_field = "domain"
            elif org_name_field == search_name or org_display_name == search_name:
                matched_field = "name"
            else:
                matched_field = "id"

        # Partial matches
        elif search_name and (
            search_name in org_name_field
            or search_name in org_display_name
            or search_name in org_domain
            or search_name in org_org_domain
            or (org_name_field and org_name_field in search_name)
        ):
            matches = True
            matched_field = "partial"

        # If we found a match, return the org_id
        if matches:
            # ALWAYS prefer the actual org_id field from the API response
            # This is the most reliable way to get the correct org_id
            if actual_org_id:
                return str(actual_org_id)

            # If no org_id field exists, try using the 'id' field
            # (but only if it's not the same as the domain)
            if org.get("id"):
                id_value = str(org.get("id"))
                # Don't use id if it's the same as domain (id might be domain)
                if id_value != str(org.get("domain", "")):
                    return id_value

            # If matched by domain, try using the domain as-is first
            # The API likely expects the full domain as org_id (e.g., "axisbank.com")
            if matched_field == "domain":
                # Prefer org_domain, then domain, then search_name
                domain_to_use = org.get("org_domain") or org.get("domain") or org_name
                if domain_to_use:
                    return str(domain_to_use)

            # Only extract base name if domain-as-is doesn't work
            # This is a fallback for APIs that don't accept domain format
            if matched_field == "domain" and "." in org_name:
                # Extract base name: "axisbank.com" -> "axisbank"
                domain_parts = org_name.split(".")
                if len(domain_parts) > 1:
                    return domain_parts[0]

            # Fallback: try to extract from org's domain field
            domain_to_extract = org.get("org_domain") or org.get("domain")
            if domain_to_extract and "." in str(domain_to_extract):
                # Extract base name: "axisbank.com" -> "axisbank"
                domain_parts = str(domain_to_extract).split(".")
                if len(domain_parts) > 1:
                    return domain_parts[0]

            # Last resort: use id field if it exists and is different from domain
            if org.get("id") and org.get("id") != org.get("domain"):
                id_value = str(org.get("id"))
                # If id also looks like a domain, extract base name
                if "." in id_value:
                    domain_parts = id_value.split(".")
                    if len(domain_parts) > 1:
                        return domain_parts[0]
                return id_value

            # If all else fails and search_name looks like a domain, extract it
            # This is the most reliable fallback
            if "." in org_name:
                domain_parts = org_name.split(".")
                if len(domain_parts) > 1:
                    return domain_parts[0]

    # Final fallback: if search_name itself is a domain, extract base name
    # This handles cases where no org was matched but search_name is a domain
    if "." in org_name:
        domain_parts = org_name.split(".")
        if len(domain_parts) > 1:
            return domain_parts[0]

    # If no match found
    st.error(f"❌ Could not find org '{org_name}'")
    return None


def get_providers_for_org(org_name: str, env: str = "prod") -> List[Dict[str, str]]:
    """Get list of providers for a specific organization.

    Args:
        org_name: Organization name
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        List of provider dicts with 'name' and 'connection' keys
    """
    org_id = get_org_id_by_name(org_name, env)
    if not org_id:
        error_msg = (
            f"⚠️ Organization '{org_name}' not found. "
            "Please check the organization name or try selecting "
            "a different organization."
        )
        st.error(error_msg)
        return []

    # Validate that we're not using the admin org_id
    try:
        admin_org_id = st.secrets.get(env, {}).get("org_id", "")
        if org_id == admin_org_id and org_name.lower() != admin_org_id.lower():
            warning_msg = (
                f"⚠️ Warning: Organization '{org_name}' matched to "
                f"admin org '{admin_org_id}'. This may be incorrect. "
                "Please verify the organization name."
            )
            st.warning(warning_msg)
    except Exception:
        pass  # If we can't check, continue anyway

    try:
        org_data = _get_org_full_data(org_id, env)
        workspaces = org_data.get("workspaces", [])
        connections_by_workspace = org_data.get("connections", {})

        if not workspaces:
            st.info(f"No workspaces found for {org_name}")
            return []

        # Build provider/connection list
        provider_list = []
        for workspace in workspaces:
            # Ensure workspace is a dict, not a string
            if not isinstance(workspace, dict):
                logger.warning(f"Skipping invalid workspace format: {type(workspace)}")
                continue

            workspace_id = workspace.get("id") or workspace.get("workspace_id")
            workspace_name = workspace.get("name", workspace_id)

            # Get connections for this workspace
            connections = connections_by_workspace.get(workspace_id, [])
            # Skip workspaces with no connections - they can't be used
            if not connections:
                continue

            # Only add entries for workspaces that have connections
            for connection in connections:
                # After normalization, connections should always be dicts
                if not isinstance(connection, dict):
                    logger.warning(
                        f"Unexpected connection format after normalization: {type(connection)}"
                    )
                    continue

                connection_id = connection.get("id")
                connection_name = connection.get("name", connection_id)

                # Get provider from connection (channel_provider field)
                # Default to "exotel" if not specified
                channel_provider = (
                    connection.get("channel_provider")
                    or connection.get("provider")
                    or "exotel"
                )

                # Skip if connection_id is empty or None
                if not connection_id or not str(connection_id).strip():
                    logger.warning(f"Skipping connection with empty id: {connection}")
                    continue

                # Create entry for each connection
                provider_list.append(
                    {
                        "name": f"{workspace_name} - {connection_name}",
                        "connection": str(connection_id),
                        "workspace_id": str(workspace_id) if workspace_id else "",
                        "workspace_name": str(workspace_name),
                        "provider_name": str(channel_provider),
                    }
                )

        return provider_list
    except Exception as e:
        error_msg = f"Failed to fetch providers/connections for {org_name}: {e}"
        st.error(error_msg)
        return []


def build_api_url(
    org_name: str,
    connection_id: str,
    workspace_id: str = None,
    provider: str = "exotel",
    env: str = "prod",
) -> str:
    """Build the API URL for a specific org, workspace, and connection.

    Args:
        org_name: Organization name
        connection_id: Connection ID
        workspace_id: Workspace ID (if None, will try to find it from connection)
        provider: Provider name (default: "exotel")
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        API URL string
    """
    org_id = get_org_id_by_name(org_name, env)
    if not org_id:
        return ""

    # If workspace_id not provided, try to find it from the connection
    if not workspace_id:
        try:
            org_data = _get_org_full_data(org_id, env)
            workspaces = org_data.get("workspaces", [])
            connections_by_workspace = org_data.get("connections", {})

            # Find which workspace contains this connection and get provider
            found_provider = provider  # Use provided provider as default
            for ws_id, connections in connections_by_workspace.items():
                for conn in connections:
                    # Handle both dict and string formats
                    conn_id = None
                    if isinstance(conn, dict):
                        conn_id = conn.get("id")
                        # Extract provider from connection if not provided
                        if not found_provider or found_provider == "exotel":
                            found_provider = (
                                conn.get("channel_provider")
                                or conn.get("provider")
                                or provider
                            )
                    elif isinstance(conn, str):
                        conn_id = conn

                    if conn_id == connection_id:
                        workspace_id = ws_id
                        if isinstance(conn, dict):
                            # Update provider from the actual connection
                            found_provider = (
                                conn.get("channel_provider")
                                or conn.get("provider")
                                or provider
                            )
                        break
                if workspace_id:
                    break

            # Use the found provider
            provider = found_provider

            # Fallback to first workspace if connection not found
            if not workspace_id and workspaces:
                workspace = workspaces[0]
                workspace_id = workspace.get("id") or workspace.get("workspace_id")
        except Exception:
            pass

    if not workspace_id:
        st.warning(f"Workspace ID not found for connection {connection_id}")
        return ""

    if not connection_id:
        st.warning(f"Connection ID is empty - cannot build API URL")
        return ""

    try:
        base_url = utils.get_base_url(env)
        # Build API URL for phone numbers endpoint
        # Use the provider from the connection (e.g., exotel, tata_tele)
        url = (
            f"{base_url}/api/app-authoring/orgs/{org_id}/"
            f"workspaces/{workspace_id}/channels/v2v/providers/{provider}/"
            f"connections/{connection_id}/phone-numbers"
        )
        return url
    except Exception as e:
        st.error(f"Failed to build API URL for {org_name}: {e}")
        return ""


def get_token_for_org(org_name: str, env: str = "prod") -> str:
    """Get authentication token for a specific organization.

    Uses admin credentials from secrets.toml to get a token.
    The admin token should work for all organizations.

    Args:
        org_name: Organization name
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        Authentication token string
    """
    return _get_admin_token(env)


def get_org_info(org_name: str, env: str = "prod") -> Dict:
    """Get complete information for an organization.

    Args:
        org_name: Organization name
        env: Environment name (prod, staging, qa). Defaults to 'prod'

    Returns:
        Dictionary with organization information
    """
    org_id = get_org_id_by_name(org_name, env)
    if not org_id:
        return {}

    orgs = _get_orgs_data(env)
    org_info = next(
        (org for org in orgs if org.get("id") == org_id or org.get("name") == org_name),
        {},
    )

    # Add full data
    try:
        full_data = _get_org_full_data(org_id, env)
        org_info.update(full_data)
    except Exception:
        pass

    return org_info


def clear_cache(env: str = "prod") -> None:
    """Clear cached data for the specified environment.

    Useful for refreshing data after changes.
    """
    cache_keys = [
        f"admin_token_{env}",
        f"orgs_data_{env}",
    ]

    # Clear all org-specific caches
    prefix = "org_full_data_"
    suffix = f"_{env}"
    for key in list(st.session_state.keys()):
        if isinstance(key, str):
            if key.startswith(prefix) and key.endswith(suffix):
                cache_keys.append(key)

    for key in cache_keys:
        if key in st.session_state:
            del st.session_state[key]
