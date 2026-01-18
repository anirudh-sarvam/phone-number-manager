"""Metrics display components."""

import streamlit as st
from typing import Dict, List, Tuple


def display_metrics(metrics: Dict[str, any], columns: int = 3) -> None:
    """
    Display metrics in columns.

    Args:
        metrics: Dictionary of metric name to value pairs
        columns: Number of columns to display metrics in
    """
    cols = st.columns(columns)
    for idx, (label, value) in enumerate(metrics.items()):
        with cols[idx % columns]:
            st.metric(label, value)


def display_stats(phone_numbers: set) -> None:
    """
    Display statistics about phone numbers.

    Args:
        phone_numbers: Set of phone numbers to analyze
    """
    if not phone_numbers:
        st.info("No data to display statistics.")
        return

    st.header("📊 Statistics")

    # Total count
    st.metric("Total Numbers", len(phone_numbers))

    # Count by prefix
    prefixes: Dict[str, int] = {}
    for num in phone_numbers:
        prefix = num[:5] if len(num) >= 5 else num
        prefixes[prefix] = prefixes.get(prefix, 0) + 1

    st.write("**Top 5 Prefixes:**")
    top_prefixes = sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:5]

    for prefix, count in top_prefixes:
        st.write(f"• `{prefix}...`: {count} numbers")
