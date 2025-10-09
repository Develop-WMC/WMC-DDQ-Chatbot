import streamlit as st
import ui # Import our UI module

# ============================================================================
# PAGE CONFIG - Must be the first Streamlit command
# ============================================================================
st.set_page_config(
    page_title="WMC DDQ Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded" # Start with sidebar open on chat page
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []

# ============================================================================
# MAIN APPLICATION LOGIC
# ============================================================================
def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()
    
    # Simple routing based on authentication status
    if not st.session_state.authenticated:
        ui.login_page()
    else:
        ui.chat_page()

if __name__ == "__main__":
    main()
