# file: app.py

import streamlit as st
import google.generativeai as genai
import re
from pathlib import Path
import ui
import llm
import config

# ============================================================================
# PAGE CONFIG - Must be the first Streamlit command
# ============================================================================
st.set_page_config(
    page_title="WMC DDQ Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# DATA LOADING AND CACHING (Now in the main app file)
# ============================================================================

@st.cache_data
def load_asset(file_path: Path) -> str:
    """A cached function to load text-based assets."""
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        st.error(f"🚨 Asset file not found at: {file_path}. Please make sure it exists.")
        st.stop()
    except Exception as e:
        st.error(f"🚨 An error occurred while loading asset {file_path}: {e}")
        st.stop()

@st.cache_resource
def initialize_model(api_key: str, knowledge_base: str):
    """Initialize Gemini model with caching for better performance."""
    try:
        if not api_key:
            st.error("⚠️ GEMINI_API_KEY not found. Please set it in your Streamlit secrets.")
            return None
        
        genai.configure(api_key=api_key)
        
        system_instruction = f"""You are a world-class Due Diligence Assistant for Wealth Management Cube Limited (WMC). Your task is to answer user questions based ONLY on the provided knowledge base.

        【KNOWLEDGE BASE - START】
        {knowledge_base}
        【KNOWLEDGE BASE - END】

        【CRITICAL RULES OF ENGAGEMENT】
        1.  **Analyze Context:** Always consider the entire conversation history to understand the user's latest question. A follow-up question like "what about them?" refers to the previous topic.
        2.  **Knowledge is Limited:** Your knowledge is strictly confined to the text within the KNOWLEDGE BASE. Do not use any external information or make assumptions.
        3.  **Handle Vague Information Intelligently:** This is the most important rule. If the knowledge base provides a general answer (e.g., "reviewed periodically") and the user asks for a more specific detail (e.g., "is that once a year?"), you must:
            a. First, state the information you DO have from the knowledge base (e.g., "The document states it is reviewed 'periodically'.").
            b. Second, explicitly state that the specific detail the user is asking for is NOT available (e.g., "...however, it does not specify a more exact frequency like 'once a year'.").
            c. DO NOT just say "I don't have that information." You must explain what you know and what you don't know.
        4.  **Handle "Upon Request" Information:** If the knowledge base says something "will be provided upon request" (like an ownership chart), and the user asks for it, you must explain that the document states it needs to be requested and is not available within your current dataset.
        5.  **Absolute Fallback:** If, and only if, you genuinely cannot find any relevant information for the user's question in the entire knowledge base after analyzing the context, then use the exact fallback phrase: "I don't have that specific information in our DDQ documents. Please contact our Compliance Officer, Peter Lau, at peterlau@wmcubehk.com or +852 3854 6419 for more details."
        """
        
        model = genai.GenerativeModel(
            model_name=config.MODEL_NAME,
            generation_config=config.GENERATION_CONFIG,
            safety_settings=config.SAFETY_SETTINGS,
            system_instruction=system_instruction
        )
        return model
    except Exception as e:
        st.error(f"❌ Failed to initialize model: {e}")
        return None

@st.cache_data
def parse_qa_from_kb(knowledge_base: str) -> dict:
    """
    Parses the knowledge base markdown file into a dictionary of
    normalized questions and their answers.
    """
    qa_dict = {}
    parts = knowledge_base.split("\n**Question:**")
    for part in parts[1:]:
        qa_split = part.split("\n**Answer:**")
        if len(qa_split) == 2:
            question = qa_split[0].strip()
            answer = qa_split[1].strip()
            normalized_question = re.sub(r'[?.,]$', '', question.lower().strip())
            qa_dict[normalized_question] = answer
    return qa_dict

# ============================================================================
# MAIN APPLICATION LOGIC
# ============================================================================

def main():
    """Main function to run the Streamlit app."""
    
    # --- Load all necessary configurations and assets ---
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("🚨 GEMINI_API_KEY not found in st.secrets. Please add it to your .streamlit/secrets.toml file.")
        st.stop()

    css_styles = load_asset(config.ASSETS_DIR / "style.css")
    knowledge_base = load_asset(config.ASSETS_DIR / "knowledge_base.md")
    
    # --- Initialize model and parse KB (these are cached) ---
    model = initialize_model(api_key, knowledge_base)
    qa_dict = parse_qa_from_kb(knowledge_base)

    if model is None:
        st.stop()

    # --- Session State Initialization ---
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # --- Page Routing ---
    if not st.session_state.authenticated:
        ui.login_page(css_styles, config.MODEL_NAME)
    else:
        ui.chat_page(
            css_content=css_styles,
            qa_dict=qa_dict,
            model=model,
            model_name=config.MODEL_NAME,
            temp=config.GENERATION_CONFIG['temperature']
        )

if __name__ == "__main__":
    main()
