"""Browse Available Numbers page."""

import streamlit as st
import pandas as pd
from datetime import datetime


def render_browse_numbers_page() -> None:
    """Render the Browse Available Numbers page."""
    st.header("Browse Available Numbers")

    if st.session_state.numbers_loaded and st.session_state.phone_numbers:

        # Search and filter
        col1, col2 = st.columns([2, 1])

        with col1:
            search_term = st.text_input(
                "🔍 Search/Filter:",
                placeholder="Enter prefix or search term (e.g., +9155)",
                help="Filter numbers by prefix or search term",
            )

        with col2:
            items_per_page = st.selectbox(
                "Items per page:", [10, 25, 50, 100, 500], index=2
            )

        # Filter numbers
        filtered_numbers = sorted(st.session_state.phone_numbers)
        if search_term:
            filtered_numbers = [n for n in filtered_numbers if search_term in n]

        # Display results
        st.write(f"**Showing {len(filtered_numbers)} numbers**")

        # Create DataFrame
        df = pd.DataFrame(filtered_numbers, columns=["Phone Number"])
        df.index = df.index + 1  # Start index from 1

        # Display with pagination
        st.dataframe(df.head(items_per_page), height=400)

        # Download button
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=(
                f"phone_numbers_" f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            ),
            mime="text/csv",
            width="stretch",
        )
    else:
        st.info("No data loaded. Please refresh from API using the sidebar.")
