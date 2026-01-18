"""Styled message boxes for consistent UI."""

import streamlit as st


def success_box(title: str, message: str) -> None:
    """
    Display a success message box.

    Args:
        title: Title of the message
        message: Message content
    """
    st.markdown(
        f"""
        <div class="success-box">
            <h3>✅ {title}</h3>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def error_box(title: str, message: str) -> None:
    """
    Display an error message box.

    Args:
        title: Title of the message
        message: Message content
    """
    st.markdown(
        f"""
        <div class="error-box">
            <h3>❌ {title}</h3>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def warning_box(title: str, message: str) -> None:
    """
    Display a warning message box.

    Args:
        title: Title of the message
        message: Message content
    """
    st.markdown(
        f"""
        <div style="background-color: #fff3cd; border: 1px solid #ffc107;
             color: #856404; padding: 1rem; border-radius: 0.5rem;
             margin: 1rem 0;">
            <h3>⚠️ {title}</h3>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_box(title: str, message: str) -> None:
    """
    Display an info message box.

    Args:
        title: Title of the message
        message: Message content
    """
    st.markdown(
        f"""
        <div style="background-color: #d1ecf1; border: 1px solid #bee5eb;
             color: #0c5460; padding: 1rem; border-radius: 0.5rem;
             margin: 1rem 0;">
            <h3>ℹ️ {title}</h3>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
