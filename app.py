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
# DATA LOADING AND CACHING
# ============================================================================

@st.cache_data
def load_asset(file_path: Path) -> str:
    """A cached function to load text-based assets from a file path."""
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

### MODIFICATION ###: Renamed and generalized the parsing function.
@st.cache_data
def parse_qa_from_markdown(knowledge_base_content: str) -> dict:
    """
    Parses a knowledge base string in Markdown format into a dictionary of
    normalized questions and their answers. It handles multi-line answers.
    """
    qa_dict = {}
    # Split the content by the question marker. This ignores anything before the first question.
    parts = knowledge_base_content.split("\n**Question:**")
    for part in parts[1:]:
        # Split each part into question and answer. The answer marker is the delimiter.
        qa_split = part.split("\nAnswer:")
        if len(qa_split) == 2:
            question = qa_split[0].strip()
            answer = qa_split[1].strip()
            
            # Normalize the question to use as a dictionary key: lowercase and remove trailing punctuation.
            normalized_question = re.sub(r'[?.,]$', '', question.lower().strip())
            qa_dict[normalized_question] = answer
    return qa_dict

# ============================================================================
# MAIN APPLICATION LOGIC
# ============================================================================

def main():
    """Main function to run the Streamlit app."""
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("🚨 GEMINI_API_KEY not found in st.secrets. Please add it to your .streamlit/secrets.toml file.")
        st.stop()

    css_styles = load_asset(config.ASSETS_DIR / "style.css")
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if not st.session_state.authenticated:
        ui.login_page(css_styles, config.MODEL_NAME)
    else:
        ### MODIFICATION ###: Updated the sidebar to accept Markdown files.
        st.sidebar.title("Knowledge Base Options")
        uploaded_file = st.sidebar.file_uploader(
            "Upload Knowledge Base File",
            type=["md", "txt"],
            help="Upload a Markdown (.md) or Text (.txt) file with the Q&A knowledge base."
        )

        knowledge_base_string = ""
        qa_dict = {}

        ### MODIFICATION ###: Updated the logic to handle uploaded text/markdown files.
        if uploaded_file is not None:
            # If a file is uploaded, use it as the knowledge base
            st.sidebar.success("✅ Knowledge base loaded successfully from file!")
            
            # Read the content of the uploaded file as a string
            knowledge_base_string = uploaded_file.getvalue().decode("utf-8")
            
            # Parse the string content to create the Q&A dictionary
            qa_dict = parse_qa_from_markdown(knowledge_base_string)
            
            if not qa_dict:
                st.warning("⚠️ The uploaded file could not be parsed or is empty. Falling back to the default knowledge base.")
                # Fallback to default if parsing fails
                knowledge_base_string = load_asset(config.ASSETS_DIR / "knowledge_base.md")
                qa_dict = parse_qa_from_markdown(knowledge_base_string)
        else:
            # Otherwise, use the default markdown file
            st.sidebar.info("ℹ️ Using the default knowledge base. Upload a file to switch.")
            knowledge_base_string = load_asset(config.ASSETS_DIR / "knowledge_base.md")
            qa_dict = parse_qa_from_markdown(knowledge_base_string)
        
        # Initialize the model. This will only re-run if `knowledge_base_string` changes.
        model = initialize_model(api_key, knowledge_base_string)

        if model is None:
            st.error("Could not initialize the AI model. The application cannot proceed.")
            st.stop()

        # Render the chat page with the loaded data
        ui.chat_page(
            css_content=css_styles,
            qa_dict=qa_dict,
            model=model,
            model_name=config.MODEL_NAME,
            temp=config.GENERATION_CONFIG['temperature']
        )

if __name__ == "__main__":
    main()
