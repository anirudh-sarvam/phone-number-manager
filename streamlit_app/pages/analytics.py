"""Analytics Dashboard page."""

import streamlit as st
import pandas as pd


def render_analytics_page() -> None:
    """Render the Analytics Dashboard page."""
    st.header("Analytics Dashboard")

    # Safely access session state with defaults
    numbers_loaded = st.session_state.get("numbers_loaded", False)
    phone_numbers = st.session_state.get("phone_numbers", set())

    if numbers_loaded and phone_numbers:

        numbers_list = list(phone_numbers)

        # Basic stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Numbers", len(numbers_list))
        with col2:
            # Count unique prefixes (first 5 digits)
            prefixes = set(n[:5] for n in numbers_list if len(n) >= 5)
            st.metric("Unique Prefixes", len(prefixes))
        with col3:
            # Average length
            avg_length = sum(len(n) for n in numbers_list) / len(numbers_list)
            st.metric("Avg. Length", f"{avg_length:.1f}")

        st.divider()

        # Prefix distribution
        st.subheader("📊 Distribution by Prefix")

        col1, col2 = st.columns(2)

        with col1:
            # Count by first 4 digits (area code)
            prefix_4 = {}
            for num in numbers_list:
                if len(num) >= 4:
                    prefix = num[:4]
                    prefix_4[prefix] = prefix_4.get(prefix, 0) + 1

            top_10 = sorted(prefix_4.items(), key=lambda x: x[1], reverse=True)[:10]
            df_prefix = pd.DataFrame(top_10, columns=["Prefix", "Count"])

            st.write("**Top 10 by First 4 Digits:**")
            st.bar_chart(df_prefix.set_index("Prefix"))

        with col2:
            # Count by state code (assuming +91 is India)
            state_codes = {}
            for num in numbers_list:
                if num.startswith("+91") and len(num) >= 6:
                    # Extract state code (next 2-4 digits after +91)
                    state = num[3:6]
                    state_codes[state] = state_codes.get(state, 0) + 1

            top_10_states = sorted(
                state_codes.items(), key=lambda x: x[1], reverse=True
            )[:10]
            df_states = pd.DataFrame(top_10_states, columns=["Code", "Count"])

            st.write("**Top 10 by Area Code:**")
            st.bar_chart(df_states.set_index("Code"))

        # Detailed breakdown
        st.divider()
        st.subheader("📈 Detailed Breakdown")

        breakdown = []
        for prefix, count in sorted(prefix_4.items(), key=lambda x: x[1], reverse=True)[
            :20
        ]:
            percentage = (count / len(numbers_list)) * 100
            breakdown.append(
                {"Prefix": prefix, "Count": count, "Percentage": f"{percentage:.2f}%"}
            )

        df_breakdown = pd.DataFrame(breakdown)
        st.dataframe(df_breakdown, hide_index=True)
    else:
        st.info("No data loaded. Please refresh from API using the sidebar.")
