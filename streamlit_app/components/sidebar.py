"""Sidebar component for the application."""

import streamlit as st
from datetime import datetime
from pathlib import Path

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
    with st.sidebar:
        st.header("⚙️ Settings")

        # Organization and Provider Selection
        st.subheader("🏢 Select Organization & Provider")

        # Initialize session state for org/provider selection
        if "selected_org" not in st.session_state:
            st.session_state.selected_org = get_org_list()[0]
        if "selected_provider_idx" not in st.session_state:
            st.session_state.selected_provider_idx = None  # No default selection

        # Organization dropdown
        org_list = get_org_list()
        selected_org = st.selectbox(
            "Organization:",
            org_list,
            index=org_list.index(st.session_state.selected_org),
            key="org_selectbox",
        )

        # Update selected org if changed
        if selected_org != st.session_state.selected_org:
            st.session_state.selected_org = selected_org
            st.session_state.selected_provider_idx = None  # Reset to no selection
            st.session_state.numbers_loaded = False  # Clear loaded data
            st.session_state.phone_numbers = set()  # Clear phone numbers
            st.session_state.last_refresh = None  # Clear last refresh time
            st.session_state.current_api_url = None  # Clear API URL
            st.session_state.current_token = None  # Clear token
            st.rerun()

        # Provider dropdown
        providers = get_providers_for_org(selected_org)
        if providers:
            provider_names = ["-- Select a Provider --"] + [p["name"] for p in providers]

            # Get current index (add 1 to account for placeholder)
            current_idx = (st.session_state.selected_provider_idx + 1) if st.session_state.selected_provider_idx is not None else 0

            # Use org name in key to force reset when org changes
            selected_provider_display_idx = st.selectbox(
                "Provider:",
                range(len(provider_names)),
                format_func=lambda x: provider_names[x],
                index=current_idx,  # Use actual index, not always 0
                key=f"provider_selectbox_{selected_org}",  # Dynamic key based on org
            )

            # Convert display index to actual provider index (subtract 1 for placeholder)
            selected_provider_idx = selected_provider_display_idx - 1 if selected_provider_display_idx > 0 else None

            # Update selected provider if changed
            if selected_provider_idx != st.session_state.selected_provider_idx:
                st.session_state.selected_provider_idx = selected_provider_idx
                st.session_state.numbers_loaded = False  # Clear loaded data
                st.session_state.phone_numbers = set()  # Clear phone numbers
                st.session_state.last_refresh = None  # Clear last refresh time
                st.rerun()

            # Only set current configuration if a provider is selected
            if selected_provider_idx is not None:
                current_provider = providers[selected_provider_idx]
                st.session_state.current_api_url = build_api_url(
                    selected_org, current_provider["connection"]
                )
                st.session_state.current_token = get_token_for_org(selected_org)

                # Show current selection info
                with st.expander("📋 Current Configuration"):
                    st.write(f"**Organization:** {selected_org}")
                    st.write(f"**Provider:** {current_provider['name']}")
                    st.write(f"**Connection:** `{current_provider['connection']}`")
            else:
                # No provider selected
                st.session_state.current_api_url = None
                st.session_state.current_token = None
                st.info("👆 Please select a provider to continue")

        st.divider()

        # Initialize session state
        if "numbers_loaded" not in st.session_state:
            st.session_state.numbers_loaded = False
        if "phone_numbers" not in st.session_state:
            st.session_state.phone_numbers = set()
        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = None

        # Load data on first run
        if not st.session_state.numbers_loaded:
            st.info("📡 Click 'Refresh from API' to fetch real phone numbers.\n\n"
                   "Note: Data will only be stored in memory (session) for security.")

        # Refresh button (only enabled if provider is selected)
        provider_selected = st.session_state.get("selected_provider_idx") is not None

        if st.button(
            "🔄 Refresh from API",
            use_container_width=True,
            disabled=not provider_selected,
            help="Select a provider first" if not provider_selected else "Fetch phone numbers from API"
        ):
            with st.spinner("Fetching phone numbers from API..."):
                try:
                    # Use selected org/provider configuration
                    api_url = st.session_state.get("current_api_url")
                    token = st.session_state.get("current_token")

                    if not api_url or not token:
                        st.error("⚠️ Please select an organization and provider first.")
                        return

                    numbers = PhoneNumberAPI.fetch_all_available_numbers(
                        api_url=api_url,
                        token=token
                    )

                    if not numbers or len(numbers) == 0:
                        st.error(
                            "❌ **API Error: No numbers fetched**\n\n"
                            "This usually means:\n"
                            "- 401 Unauthorized: Your token is expired or invalid\n"
                            "- 404 Not Found: The API endpoint URL is incorrect\n\n"
                            "Check your `.env` file configuration."
                        )
                    else:
                        # Load numbers into session state (memory only)
                        st.session_state.phone_numbers = numbers
                        st.session_state.numbers_loaded = True
                        st.session_state.last_refresh = datetime.now()

                        # Delete CSV file for security (data only in memory)
                        if Path(config.CSV_FILE).exists():
                            Path(config.CSV_FILE).unlink()

                        st.success(f"✅ Loaded {len(numbers)} numbers from **{st.session_state.selected_org}**!")
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
