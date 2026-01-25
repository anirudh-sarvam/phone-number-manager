"""
Authentication module for admin access.
"""

import streamlit as st
import hashlib
import os
from pathlib import Path
import dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
dotenv.load_dotenv(dotenv_path=env_path, override=True)

# Admin credentials - Load from environment variables
ENV_USERNAME = os.getenv("ADMIN_USERNAME")
ENV_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

# Check if credentials are configured
if not ENV_USERNAME or not ENV_PASSWORD_HASH:
    import warnings

    warnings.warn(
        "Admin credentials not configured. "
        "Set ADMIN_USERNAME and ADMIN_PASSWORD_HASH in .env file."
    )


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(username: str, password: str) -> bool:
    """
    Check if username and password are correct.

    Args:
        username: Username to check
        password: Password to check

    Returns:
        True if credentials are valid, False otherwise
    """
    # Check if credentials are configured
    if not ENV_USERNAME or not ENV_PASSWORD_HASH:
        return False

    if username != ENV_USERNAME:
        return False

    password_hash = hash_password(password)
    return password_hash == ENV_PASSWORD_HASH


def login_page():
    """Render the login page."""
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
    if not ENV_USERNAME or not ENV_PASSWORD_HASH:
        st.error(
            "⚠️ Admin credentials not configured. "
            "Please set ADMIN_USERNAME and ADMIN_PASSWORD_HASH "
            "in .env file."
        )
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
                st.success("✅ Login successful!")
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
