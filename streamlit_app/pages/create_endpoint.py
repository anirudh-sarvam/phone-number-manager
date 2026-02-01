"""Create Endpoint page."""

import streamlit as st

from ..utils.helpers import is_number_available
from ..utils.api_client import EndpointAPI
from ..components.styled_boxes import success_box, error_box


def render_single_endpoint_tab() -> None:
    """Render the single endpoint creation tab."""
    st.subheader("Create Single Endpoint")

    # Check if organization and provider are selected
    if not st.session_state.get("current_api_url") or not st.session_state.get(
        "current_token"
    ):
        st.warning(
            "⚠️ Please select an **Organization** and **Provider** from the sidebar first."
        )
        return

    single_number = st.text_input(
        "Phone Number:",
        placeholder="+915551234567",
        help="Enter a phone number to register as an endpoint",
        key="single_number_input",
    )

    # Option to check availability first
    check_before_create = st.checkbox(
        "Check availability before creating",
        value=True,
        help="Verify the number is available in the database "
        "before attempting to create endpoint",
    )

    if st.button("🚀 Create Endpoint", type="primary", width="stretch"):
        if single_number:
            # Check availability first if enabled
            if check_before_create:
                # Check if we have numbers loaded
                if not st.session_state.get("numbers_loaded", False):
                    st.warning(
                        "⚠️ No data loaded. Please click 'Refresh from API' in the sidebar first."
                    )
                    return

                with st.spinner("Checking availability..."):
                    is_available = is_number_available(
                        single_number, numbers_set=st.session_state.phone_numbers
                    )

                if not is_available:
                    error_box(
                        "Number Not Available",
                        f"<strong>{single_number}</strong> is not available "
                        "in the database. Please choose a number from the "
                        "available list.",
                    )
                    return

                st.success(f"✅ **{single_number}** is available!")

            # Proceed with creation
            with st.spinner("Creating endpoint..."):
                try:
                    result = EndpointAPI.create_single_endpoint(
                        single_number,
                        base_url=st.session_state.get("current_api_url"),
                        token=st.session_state.get("current_token"),
                        verbose=False,
                    )
                    success_box(
                        "Endpoint Created Successfully!",
                        f"Phone number <strong>{single_number}</strong> "
                        "has been registered as an endpoint.",
                    )
                    with st.expander("View API Response"):
                        st.json(result)
                except Exception as e:
                    error_msg = str(e)

                    # Check if it's the "already exists" case
                    if "already exist" in error_msg.lower():
                        st.warning(
                            f"⚠️ **{single_number}** already exists as an endpoint!"
                        )
                        st.info(
                            "💡 **Possible reasons:**\n"
                            "- This number is already registered as an endpoint in this provider\n"
                            "- The number might be registered in a different provider for this organization\n"
                            "- Try checking with a different phone number"
                        )
                    else:
                        st.error(f"❌ Failed to create endpoint")
                        st.code(error_msg, language="text")
        else:
            st.warning("Please enter a phone number.")


def render_bulk_endpoint_tab() -> None:
    """Render the bulk endpoint creation tab."""
    st.subheader("Create Multiple Endpoints")

    # Check if organization and provider are selected
    if not st.session_state.get("current_api_url") or not st.session_state.get(
        "current_token"
    ):
        st.warning(
            "⚠️ Please select an **Organization** and **Provider** from the sidebar first."
        )
        return

    st.write(
        "Enter multiple phone numbers (one per line) to register them " "all at once."
    )

    bulk_numbers = st.text_area(
        "Phone Numbers (one per line):",
        height=200,
        placeholder="+915551234567\n+915551234568\n+915551234569",
        help="Enter each phone number on a new line",
        key="bulk_numbers_input",
    )

    # Preview
    if bulk_numbers:
        numbers_list = [n.strip() for n in bulk_numbers.split("\n") if n.strip()]
        st.info(f"📊 Ready to create {len(numbers_list)} endpoint(s)")

        # Show preview
        with st.expander(f"Preview {len(numbers_list)} numbers"):
            for i, num in enumerate(numbers_list, 1):
                st.write(f"{i}. `{num}`")

    check_before_bulk = st.checkbox(
        "Check availability before creating",
        value=True,
        help="Verify numbers are available before attempting " "to create endpoints",
        key="check_before_bulk",
    )

    if st.button("🚀 Create All Endpoints", type="primary", width="stretch"):
        if bulk_numbers:
            numbers_list = [n.strip() for n in bulk_numbers.split("\n") if n.strip()]

            if not numbers_list:
                st.warning("No valid phone numbers found.")
                return

            # Check availability first if enabled
            if check_before_bulk:
                # Check if we have numbers loaded
                if not st.session_state.get("numbers_loaded", False):
                    st.warning(
                        "⚠️ No data loaded. Please click 'Refresh from API' in the sidebar first."
                    )
                    return

                with st.spinner(f"Checking {len(numbers_list)} numbers..."):
                    available_numbers = []
                    unavailable_numbers = []

                    for num in numbers_list:
                        if is_number_available(
                            num, numbers_set=st.session_state.phone_numbers
                        ):
                            available_numbers.append(num)
                        else:
                            unavailable_numbers.append(num)

                # Show results
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Available", len(available_numbers))
                with col2:
                    st.metric("Not Available", len(unavailable_numbers))

                if unavailable_numbers:
                    with st.expander(
                        f"⚠️ {len(unavailable_numbers)} numbers not available"
                    ):
                        for num in unavailable_numbers:
                            st.write(f"❌ `{num}`")

                if not available_numbers:
                    st.error(
                        "❌ None of the provided numbers are available "
                        "in the database."
                    )
                    return

                st.success(f"✅ Found {len(available_numbers)} available number(s)")
                numbers_to_create = available_numbers
            else:
                numbers_to_create = numbers_list

            # Create endpoints
            with st.spinner(f"Creating {len(numbers_to_create)} endpoint(s)..."):
                try:
                    result = EndpointAPI.create_bulk_endpoints(
                        numbers_to_create,
                        base_url=st.session_state.get("current_api_url"),
                        token=st.session_state.get("current_token"),
                        verbose=False,
                    )
                    success_box(
                        "Endpoints Created Successfully!",
                        f"<strong>{len(numbers_to_create)}</strong> "
                        "phone number(s) have been registered as endpoints.",
                    )
                    with st.expander("View API Response"):
                        st.json(result)
                    with st.expander("Successfully Created Numbers"):
                        for num in numbers_to_create:
                            st.write(f"✅ `{num}`")
                except Exception as e:
                    error_msg = str(e)
                    if "already exist" in error_msg.lower():
                        st.warning(
                            "⚠️ One or more numbers already exist " "as endpoints!"
                        )
                    else:
                        st.error(f"❌ Failed to create endpoints: {error_msg}")
        else:
            st.warning("Please enter at least one phone number.")


def render_create_endpoint_page() -> None:
    """Render the Create Endpoint page."""
    st.header("Create New Endpoint")
    st.write(
        "Register phone number(s) as endpoints. You can create a single "
        "endpoint or multiple endpoints at once."
    )

    # Create tabs for single and bulk creation
    subtab1, subtab2 = st.tabs(["📱 Single Endpoint", "📋 Bulk Endpoints"])

    with subtab1:
        render_single_endpoint_tab()

    with subtab2:
        render_bulk_endpoint_tab()
