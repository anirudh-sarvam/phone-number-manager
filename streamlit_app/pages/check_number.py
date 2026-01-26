"""Check Number Availability page."""

import streamlit as st
import pandas as pd

from ..utils.helpers import is_number_available
from ..components.styled_boxes import success_box, error_box


def render_check_number_page() -> None:
    """Render the Check Number Availability page."""
    st.header("Check Number Availability")

    col1, col2 = st.columns([3, 1])

    with col1:
        phone_input = st.text_input(
            "Enter phone number to check:",
            placeholder="+915559876543",
            help="Enter the phone number in any format "
            "(with or without +, spaces, dashes)",
        )

    with col2:
        check_api = st.checkbox(
            "Check API",
            value=False,
            help="Fetch fresh data from API instead of using cached data",
        )

    if st.button("🔎 Check Availability", type="primary", width="stretch"):
        if phone_input:
            # Check if we have numbers loaded
            if not st.session_state.get("numbers_loaded", False):
                st.warning(
                    "⚠️ No data loaded. Please click 'Refresh from API' in the sidebar first."
                )
            else:
                with st.spinner("Checking..."):
                    # Pass session state numbers to the check function
                    is_available = is_number_available(
                        phone_input,
                        numbers_set=st.session_state.phone_numbers,
                        refresh=check_api,
                    )

                if is_available:
                    success_box(
                        "Number Available!",
                        f"<strong>{phone_input}</strong> is available "
                        "in the database.",
                    )
                else:
                    error_box(
                        "Number Not Found",
                        f"<strong>{phone_input}</strong> is not available "
                        "in the database.",
                    )
        else:
            st.warning("Please enter a phone number.")

    # Bulk check
    st.divider()
    st.subheader("📝 Bulk Check")
    bulk_input = st.text_area(
        "Enter multiple numbers (one per line):",
        height=150,
        placeholder="+915559876543\n+915559876544\n+915559876545",
    )

    if st.button("🔎 Check All", width="stretch"):
        if bulk_input:
            # Check if we have numbers loaded
            if not st.session_state.get("numbers_loaded", False):
                st.warning(
                    "⚠️ No data loaded. Please click 'Refresh from API' in the sidebar first."
                )
            else:
                numbers_to_check = [
                    n.strip() for n in bulk_input.split("\n") if n.strip()
                ]

                with st.spinner(f"Checking {len(numbers_to_check)} numbers..."):
                    results = []
                    for num in numbers_to_check:
                        is_avail = is_number_available(
                            num, numbers_set=st.session_state.phone_numbers
                        )
                        results.append(
                            {
                                "Phone Number": num,
                                "Status": (
                                    "✅ Available" if is_avail else "❌ Not Found"
                                ),
                            }
                        )

                    df = pd.DataFrame(results)
                    st.dataframe(df, hide_index=True)

                    # Summary
                    available_count = sum(1 for r in results if "✅" in r["Status"])
                    st.success(
                        f"Found {available_count} out of " f"{len(results)} numbers"
                    )
