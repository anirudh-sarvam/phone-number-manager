"""Sidebar component for the application."""

import streamlit as st
from datetime import datetime
from pathlib import Path
import requests

from ..utils.config import config
from ..utils.api_client import PhoneNumberAPI
from ..utils.multi_org_config import (
    get_org_list,
    get_providers_for_org,
    build_api_url,
    get_token_for_org,
)


def render_sidebar() -> None:
    """Render the application sidebar with controls and statistics."""
    # Initialize session state early to prevent AttributeError in pages
    if "numbers_loaded" not in st.session_state:
        st.session_state.numbers_loaded = False
    if "phone_numbers" not in st.session_state:
        st.session_state.phone_numbers = set()
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = None

    with st.sidebar:
        st.header("⚙️ Settings")

        # Organization and Provider Selection
        st.subheader("🏢 Select Organization & Provider")

        # Initialize session state for org/provider selection
        org_list = get_org_list()

        # Organization dropdown
        if not org_list:
            warning_msg = (
                "⚠️ No organizations found. " "Please check your API configuration."
            )
            st.warning(warning_msg)
            return

        # Initialize selected_org if not set (default to None/empty)
        if "selected_org" not in st.session_state:
            st.session_state.selected_org = None

        # Validate selected_org is in the current list
        if (
            st.session_state.selected_org
            and st.session_state.selected_org not in org_list
        ):
            # Selected org no longer exists - clear selection
            st.session_state.selected_org = None
            st.session_state.selected_provider_idx = None
            st.session_state.numbers_loaded = False
            st.session_state.phone_numbers = set()
            st.session_state.last_refresh = None
            st.session_state.current_api_url = None
            st.session_state.current_token = None

        if "selected_provider_idx" not in st.session_state:
            # No default selection
            st.session_state.selected_provider_idx = None

        # Create options list with empty option at the beginning (always first)
        SELECT_ORG_PROMPT = "-- Select Organization --"
        org_options = [SELECT_ORG_PROMPT] + org_list

        # Get index of selected org (0 = empty/select prompt)
        current_selected_org = st.session_state.get("selected_org")
        if current_selected_org and current_selected_org in org_list:
            try:
                org_index = org_list.index(current_selected_org) + 1  # +1 for prompt
            except ValueError:
                org_index = 0
                st.session_state.selected_org = None
        else:
            org_index = 0  # Default to prompt option
            st.session_state.selected_org = None

        selected_org_option = st.selectbox(
            "Organization:",
            org_options,
            index=org_index,
            key="org_selectbox",
        )

        # Extract actual org name (remove the prompt option)
        if selected_org_option == SELECT_ORG_PROMPT:
            selected_org = None
        else:
            selected_org = selected_org_option

        # Update selected org if changed
        if selected_org != st.session_state.get("selected_org"):
            st.session_state.selected_org = selected_org
            # Reset to no selection
            st.session_state.selected_provider_idx = None
            # Clear loaded data
            st.session_state.numbers_loaded = False
            st.session_state.phone_numbers = set()
            st.session_state.last_refresh = None
            st.session_state.current_api_url = None
            st.session_state.current_token = None
            st.rerun()

        # Show provider dropdown only if an organization is selected
        # Check if a valid org is selected (not the prompt)
        if not selected_org:
            st.info("👆 Please select an organization first")
            st.session_state.current_api_url = None
            st.session_state.current_token = None
            st.session_state.selected_provider_idx = None
            return

        # At this point, selected_org is guaranteed to be a valid org name

        # Provider dropdown
        try:
            providers = get_providers_for_org(selected_org)
        except Exception as e:
            st.error(f"Error fetching providers: {e}")
            providers = []

        if providers:
            provider_names = ["-- Select a Provider --"] + [
                p["name"] for p in providers
            ]

            # Get current index (add 1 to account for placeholder)
            current_idx = (
                (st.session_state.selected_provider_idx + 1)
                if st.session_state.selected_provider_idx is not None
                else 0
            )

            # Use org name in key to force reset when org changes
            provider_key = f"provider_selectbox_{selected_org}"
            selected_provider_display_idx = st.selectbox(
                "Provider:",
                range(len(provider_names)),
                format_func=lambda x: provider_names[x],
                index=current_idx,  # Use actual index, not always 0
                key=provider_key,  # Dynamic key based on org
            )

            # Convert display index to actual provider index
            # (subtract 1 for placeholder)
            selected_provider_idx = (
                selected_provider_display_idx - 1
                if selected_provider_display_idx > 0
                else None
            )

            # Update selected provider if changed
            if selected_provider_idx != st.session_state.selected_provider_idx:
                st.session_state.selected_provider_idx = selected_provider_idx
                # Clear loaded data
                st.session_state.numbers_loaded = False
                st.session_state.phone_numbers = set()
                st.session_state.last_refresh = None
                st.rerun()

            # Only set current configuration if a provider is selected
            if selected_provider_idx is not None:
                current_provider = providers[selected_provider_idx]
                connection_id = current_provider.get("connection", "")
                workspace_id = current_provider.get("workspace_id")
                provider_name = current_provider.get("provider_name", "exotel")

                # Validate connection_id is not empty
                if not connection_id:
                    st.warning(
                        f"⚠️ Selected provider '{current_provider.get('name', 'Unknown')}' "
                        "has no connection ID. Please select a different provider."
                    )
                    st.session_state.current_api_url = None
                    st.session_state.current_token = None
                else:
                    if selected_org and workspace_id:  # Type guards
                        st.session_state.current_api_url = build_api_url(
                            selected_org,
                            connection_id,
                            workspace_id,
                            provider_name,
                        )
                    st.session_state.current_token = get_token_for_org(selected_org)

                # Show current selection info
                with st.expander("📋 Current Configuration"):
                    st.write(f"**Organization:** {selected_org}")
                    st.write(f"**Provider:** {current_provider['name']}")
                    st.write(f"**Connection:** `{current_provider['connection']}`")
                    st.write(f"**Workspace ID:** `{workspace_id}`")
                    st.write(f"**Channel Provider:** `{provider_name}`")
                    if st.session_state.current_api_url:
                        st.write(f"**API URL:** `{st.session_state.current_api_url}`")
                        # Verify provider in URL matches channel_provider
                        if provider_name and provider_name != "exotel":
                            if (
                                f"/providers/{provider_name}/"
                                not in st.session_state.current_api_url
                            ):
                                st.warning(
                                    f"⚠️ URL uses different provider than connection's "
                                    f"channel_provider ({provider_name})"
                                )
            else:
                # No provider selected
                st.session_state.current_api_url = None
                st.session_state.current_token = None
                st.info("👆 Please select a provider to continue")
        else:
            # No providers found - show message
            st.session_state.current_api_url = None
            st.session_state.current_token = None
            st.session_state.selected_provider_idx = None
            st.warning(
                f"⚠️ No providers found for **{selected_org}**. "
                "This organization may not have any telephony providers "
                "configured, or there was an error fetching provider data."
            )

        st.divider()

        # Check if provider is selected
        provider_selected = st.session_state.get("selected_provider_idx") is not None

        # Load data on first run (disabled - wait for user to select provider)
        if not st.session_state.numbers_loaded:
            if not provider_selected:
                info_msg = (
                    "📡 Select an organization and provider above, "
                    "then click 'Refresh from API' to fetch phone numbers.\n\n"
                    "Note: Data will only be stored in memory "
                    "(session) for security."
                )
                st.info(info_msg)
            else:
                info_msg = (
                    "📡 Click 'Refresh from API' to fetch phone numbers.\n\n"
                    "Note: Data will only be stored in memory "
                    "(session) for security."
                )
                st.info(info_msg)

        # Refresh button (only enabled if provider is selected)

        if st.button(
            "🔄 Refresh from API",
            width="stretch",
            disabled=not provider_selected,
            help=(
                "Select a provider first"
                if not provider_selected
                else "Fetch phone numbers from API"
            ),
        ):
            with st.spinner("Fetching phone numbers from API..."):
                try:
                    # Use selected org/provider configuration
                    api_url = st.session_state.get("current_api_url")
                    token = st.session_state.get("current_token")

                    if not api_url or not token:
                        error_msg = (
                            "⚠️ Please select an organization " "and provider first."
                        )
                        st.error(error_msg)
                        return

                    numbers = PhoneNumberAPI.fetch_all_available_numbers(
                        api_url=api_url, token=token
                    )

                    if not numbers or len(numbers) == 0:
                        # Check if this is a tata_tele connection (likely no phone numbers)
                        if "tata_tele" in api_url.lower():
                            connection_id = (
                                api_url.split("/connections/")[-1].split("/")[0]
                                if "/connections/" in api_url
                                else "this connection"
                            )
                            st.info(
                                f"ℹ️ **No phone numbers available**\n\n"
                                f"This `tata_tele` connection does not have any phone numbers configured.\n\n"
                                "**To fetch phone numbers:**\n"
                                "- Try selecting a different connection that uses `exotel` provider\n"
                                "- Or configure phone numbers for this connection in the Sarvam platform first"
                            )
                        else:
                            st.warning(
                                "⚠️ **No phone numbers found**\n\n"
                                "This connection does not have any phone numbers available. "
                                "Try selecting a different connection or provider."
                            )
                    else:
                        # Load numbers into session state (memory only)
                        st.session_state.phone_numbers = numbers
                        st.session_state.numbers_loaded = True
                        st.session_state.last_refresh = datetime.now()

                        # Delete CSV file for security (data only in memory)
                        if Path(config.CSV_FILE).exists():
                            Path(config.CSV_FILE).unlink()

                        success_msg = (
                            f"✅ Loaded {len(numbers)} numbers from "
                            f"**{st.session_state.selected_org}**!"
                        )
                        st.success(success_msg)
                        st.info("🔒 No CSV file - data stored only in session memory.")
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ **Error fetching from API:**\n\n{str(e)}")

        # Last refresh info
        if st.session_state.last_refresh:
            st.info(
                f"**Last updated:**\n"
                f"{st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        st.divider()

        # Statistics
        if st.session_state.numbers_loaded and st.session_state.phone_numbers:
            from .metrics import display_stats

            display_stats(st.session_state.phone_numbers)
