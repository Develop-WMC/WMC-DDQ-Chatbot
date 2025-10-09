import streamlit as st
from pathlib import Path

# --- PATHS ---
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# --- MODEL CONFIGURATION ---
MODEL_NAME = "gemini-2.0-flash-exp"
GENERATION_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 20,
    "max_output_tokens": 4096,
}
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- SECRETS ---
# Load secrets from Streamlit's secrets management
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    USERS = st.secrets["users"]
except FileNotFoundError:
    st.error("🚨 'secrets.toml' not found. Please create it in the '.streamlit' directory.")
    st.stop()
except KeyError as e:
    st.error(f"🚨 Secret '{e}' not found in 'secrets.toml'.")
    st.stop()


# --- ASSET LOADING ---
@st.cache_data
def load_asset(file_path: Path) -> str:
    """A cached function to load text-based assets."""
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        st.error(f"🚨 Asset file not found at: {file_path}")
        st.stop()
    except Exception as e:
        st.error(f"🚨 An error occurred while loading asset {file_path}: {e}")
        st.stop()

# Load Knowledge Base and CSS
KNOWLEDGE_BASE = load_asset(ASSETS_DIR / "knowledge_base.md")
CSS_STYLES = load_asset(ASSETS_DIR / "style.css")
