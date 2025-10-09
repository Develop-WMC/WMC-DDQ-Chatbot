import streamlit as st
import google.generativeai as genai
import config
import re

@st.cache_resource
def initialize_model():
    """Initialize Gemini model with caching for better performance."""
    try:
        if not config.GEMINI_API_KEY:
            st.error("⚠️ GEMINI_API_KEY not found. Please set it in your Streamlit secrets.")
            return None
            
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        model = genai.GenerativeModel(
            model_name=config.MODEL_NAME,
            generation_config=config.GENERATION_CONFIG,
            safety_settings=config.SAFETY_SETTINGS
        )
        return model
    except Exception as e:
        st.error(f"❌ Failed to initialize model: {e}")
        return None

@st.cache_data
def _parse_qa_from_kb():
    """
    Parses the knowledge base markdown file into a dictionary of
    normalized questions and their answers.
    """
    qa_dict = {}
    # Split the entire text by the question marker
    parts = config.KNOWLEDGE_BASE.split("\n**Question:**")
    for part in parts[1:]:  # Skip the first part as it has no preceding question
        # Split each part into question and answer
        qa_split = part.split("\n**Answer:**")
        if len(qa_split) == 2:
            question = qa_split[0].strip()
            answer = qa_split[1].strip()
            
            # Normalize the question to use as a dictionary key: lowercase, strip whitespace
            # and remove trailing punctuation like '?' or '.'
            normalized_question = re.sub(r'[?.]$', '', question.lower().strip())
            qa_dict[normalized_question] = answer
            
    return qa_dict

def _get_gemini_semantic_response(question: str) -> str:
    """
    Gets a response from the Gemini model using the full context.
    This is the fallback for when no exact match is found.
    """
    try:
        model = initialize_model()
        if not model:
            return "Error: Model initialization failed. Please check your API key."
        
        prompt = f"""You are a Due Diligence Assistant for Wealth Management Cube Limited (WMC).

        【CRITICAL RULES】
        1. ❌ ONLY use information from the KNOWLEDGE BASE below.
        2. ❌ DO NOT make up, guess, or use external knowledge.
        3. ❌ If the information is NOT in the KNOWLEDGE BASE, you MUST say exactly: "I don't have that specific information in our DDQ documents. Please contact our Compliance Officer, Peter Lau, at peterlau@wmcubehk.com or +852 3854 6419 for more details."
        4. ✅ Be professional, concise, and accurate.

        【KNOWLEDGE BASE - START】
        {config.KNOWLEDGE_BASE}
        【KNOWLEDGE BASE - END】

        【USER QUESTION】
        {question}

        【YOUR ANSWER】
        """
        
        response = model.generate_content(prompt)
        
        if not response or not response.parts:
            block_reason = getattr(response.prompt_feedback, 'block_reason', 'Unknown reason')
            return f"⚠️ Response was blocked: {block_reason}. Please rephrase your question."
        
        return response.text

    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg:
            return "⏱️ Request timed out. Please try again or contact our Compliance Officer."
        elif "api key" in error_msg or "api_key" in error_msg:
            return "❌ API key error. Please check your Gemini API configuration."
        elif "quota" in error_msg or "limit" in error_msg:
            return "❌ API quota exceeded. Please try again later or contact support."
        return f"❌ An unexpected error occurred: {e}\nPlease contact our Compliance Officer for assistance."

def get_response(question: str) -> str:
    """
    Provides an answer using a hybrid approach:
    1. Tries to find an exact match for the question in the knowledge base.
    2. If no exact match is found, falls back to the AI for a semantic search.
    """
    # Get the pre-parsed Q&A dictionary
    qa_dict = _parse_qa_from_kb()
    
    # Normalize the user's question for a robust lookup
    # (lowercase, strip whitespace, remove trailing punctuation)
    normalized_q = re.sub(r'[?.]$', '', question.lower().strip())

    # Check if the normalized question exists as a key in our dictionary
    if normalized_q in qa_dict:
        # If it exists, we have an exact match! Return the answer directly.
        print(f"✅ Exact match found for: '{question}'") # For debugging in console
        return qa_dict[normalized_q]
    else:
        # If no exact match, use the AI to understand the question semantically.
        print(f"⚠️ No exact match. Using AI for: '{question}'") # For debugging in console
        return _get_gemini_semantic_response(question)
