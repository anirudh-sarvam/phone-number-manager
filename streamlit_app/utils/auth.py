"""
Authentication module for admin access.
Uses credentials from secrets.toml (not .env).
"""

import hashlib
from typing import Optional, Tuple

import streamlit as st


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def _get_admin_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Get admin credentials from secrets.toml.

    Returns:
        Tuple of (username, password_hash) or (None, None) if not configured
    """
    try:
        username = st.secrets.get("admin", {}).get("username")
        password_hash = st.secrets.get("admin", {}).get("password_hash")
        return username, password_hash
    except Exception:
        return None, None


def check_password(username: str, password: str) -> bool:
    """
    Check if username and password are correct.

    Args:
        username: Username to check
        password: Password to check

    Returns:
        True if credentials are valid, False otherwise
    """
    admin_username, admin_password_hash = _get_admin_credentials()

    # Check if credentials are configured
    if not admin_username or not admin_password_hash:
        return False

    if username != admin_username:
        return False

    password_hash = hash_password(password)
    return password_hash == admin_password_hash


def login_page():
    """Render the login page."""
    # Check if already authenticated (shouldn't happen, but safety check)
    if st.session_state.get("authenticated", False):
        return

    st.markdown(
        """
        <style>
        .login-container {
            max-width: 400px;
            margin: 50px auto;
            padding: 1.5rem;
            border-radius: 10px;
            background-color: #f0f2f6;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            color: #1f77b4;
            margin-bottom: 1rem;
            font-size: 1.8rem;
        }
        .login-subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-header">🔐 Admin Login</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="login-subtitle">Phone Number Manager</p>',
        unsafe_allow_html=True,
    )

    # Check if credentials are configured
    admin_username, admin_password_hash = _get_admin_credentials()
    if not admin_username or not admin_password_hash:
        error_msg = (
            "⚠️ Admin credentials not configured. "
            "Please set admin.username and admin.password_hash "
            "in .streamlit/secrets.toml file."
        )
        st.error(error_msg)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter password"
        )
        submit = st.form_submit_button("Login", width="stretch", type="primary")

        if submit:
            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.markdown("</div>", unsafe_allow_html=True)
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)


def logout():
    """Logout the current user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


def require_auth():
    """
    Decorator/function to require authentication.
    Call this at the start of your main app.

    Returns:
        True if authenticated, False otherwise
    """
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None

    # Check if user is authenticated
    if not st.session_state.authenticated:
        login_page()
        return False

    return True


def get_current_user() -> str:
    """Get the current logged-in username."""
    return st.session_state.get("username", "")
