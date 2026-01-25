"""
Phone Number Manager - Main Application

A professional Streamlit application for managing phone numbers and endpoints.
"""

import streamlit as st

from streamlit_app.utils.config import config
from streamlit_app.utils.auth import require_auth, logout, get_current_user
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.pages import (
    render_check_number_page,
    render_browse_numbers_page,
    render_create_endpoint_page,
    render_analytics_page,
)


def apply_custom_css() -> None:
    """Apply custom CSS styling to the application."""
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
            margin-top: 0.5rem;
        }
        .metric-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .success-box {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .error-box {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title=config.PAGE_TITLE,
        page_icon=config.PAGE_ICON,
        layout=config.LAYOUT,  # type: ignore
        initial_sidebar_state="expanded",
    )

    # Apply custom styling
    apply_custom_css()

    # Check authentication
    if not require_auth():
        return  # Show login page if not authenticated

    # Add logout button in sidebar
    with st.sidebar:
        st.divider()
        current_user = get_current_user()
        st.markdown(f"👤 **Logged in as:** {current_user}")
        if st.button("🚪 Logout", width="stretch"):
            logout()

    # Main header
    st.markdown(
        f'<div class="main-header">{config.PAGE_ICON} ' f"{config.PAGE_TITLE}</div>",
        unsafe_allow_html=True,
    )

    # Render sidebar
    render_sidebar()

    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Check Number", "📋 Browse Numbers", "➕ Create Endpoint", "📊 Analytics"]
    )

    with tab1:
        render_check_number_page()

    with tab2:
        render_browse_numbers_page()

    with tab3:
        render_create_endpoint_page()

    with tab4:
        render_analytics_page()

    # Footer
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; color: #666; padding: 0.5rem;">
            <p>Phone Number Manager | Built with Streamlit</p>
        </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
