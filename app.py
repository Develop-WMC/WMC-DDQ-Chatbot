# file: app.py

import streamlit as st
import google.generativeai as genai
import re
from pathlib import Path
import ui
import llm
import config
import utils  # Import the new utils file

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
# DATA LOADING AND CACHING (No changes needed in these functions)
# ============================================================================

@st.cache_data
def load_asset(file_path: Path) -> str:
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
# MAIN APPLICATION LOGIC (MODIFIED)
# ============================================================================

def main():
    """Main function to run the Streamlit app."""
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("🚨 GEMINI_API_KEY not found in st.secrets. Please add it to your .streamlit/secrets.toml file.")
        st.stop()

    css_styles = load_asset(config.ASSETS_DIR / "style.css")

    # --- Session State Initialization ---
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    # Add session state to track the uploaded file's ID to detect changes
    if 'uploaded_file_id' not in st.session_state:
        st.session_state.uploaded_file_id = None

    # --- Page Routing ---
    if not st.session_state.authenticated:
        ui.login_page(css_styles, config.MODEL_NAME)
    else:
        # --- Sidebar and File Upload Handling ---
        # Render the sidebar and get the uploaded file object
        uploaded_file = ui._render_sidebar(config.MODEL_NAME, config.GENERATION_CONFIG['temperature'])

        knowledge_base = None
        qa_dict = {}

        # --- Dynamic Knowledge Base Logic ---
        if uploaded_file is not None:
            # If a new file is uploaded, clear old chat history
            if st.session_state.uploaded_file_id != uploaded_file.id:
                st.session_state.messages = []
                st.session_state.uploaded_file_id = uploaded_file.id
            
            # Parse the uploaded file to get its text content
            knowledge_base = utils.parse_uploaded_file(uploaded_file)
            # For custom uploads, we disable the exact-match QA dictionary
            qa_dict = {}
        else:
            # If no file is uploaded, fall back to the default knowledge base
            if st.session_state.uploaded_file_id is not None:
                st.session_state.messages = [] # Clear history when file is removed
            st.session_state.uploaded_file_id = None

            knowledge_base = load_asset(config.ASSETS_DIR / "knowledge_base.md")
            # For the default KB, we parse the Q&A for the hybrid search
            qa_dict = parse_qa_from_kb(knowledge_base)

        # --- Initialize model (cached) ---
        # The model will be re-initialized only if the `knowledge_base` text changes.
        if knowledge_base:
            model = initialize_model(api_key, knowledge_base)
            if model is None:
                st.error("Model could not be initialized. Please check the logs.")
                st.stop()
        else:
            # This can happen if file parsing fails
            st.warning("Could not load a knowledge base. Please upload a valid document or ensure 'knowledge_base.md' exists.")
            st.stop()
            
        # --- Render the main chat page ---
        ui.chat_page(
            css_content=css_styles,
            qa_dict=qa_dict,
            model=model,
            model_name=config.MODEL_NAME,
            temp=config.GENERATION_CONFIG['temperature'],
            uploaded_file=uploaded_file # Pass the file object to the UI
        )

if __name__ == "__main__":
    main()
