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
    parts = config.KNOWLEDGE_BASE.split("\n**Question:**")
    for part in parts[1:]:
        qa_split = part.split("\n**Answer:**")
        if len(qa_split) == 2:
            question = qa_split[0].strip()
            answer = qa_split[1].strip()
            normalized_question = re.sub(r'[?.]$', '', question.lower().strip())
            qa_dict[normalized_question] = answer
            
    return qa_dict

# --- THIS IS THE FUNCTION WE ARE UPDATING ---
def _get_gemini_semantic_response(question: str) -> str:
    """
    Gets a response from the Gemini model using Chain of Thought prompting.
    This is the fallback for when no exact match is found.
    """
    try:
        model = initialize_model()
        if not model:
            return "Error: Model initialization failed. Please check your API key."
        
        # --- UPDATED PROMPT WITH CHAIN OF THOUGHT ---
        prompt = f"""You are a world-class Due Diligence Assistant for Wealth Management Cube Limited (WMC). Your task is to answer user questions based ONLY on the provided knowledge base.

        【KNOWLEDGE BASE - START】
        {config.KNOWLEDGE_BASE}
        【KNOWLEDGE BASE - END】

        【REASONING PROCESS - Follow these steps before answering】
        1.  **Analyze the User's Question:** Identify the core keywords and intent of the user's question. For example, if the user asks "Tell me about your process for overseeing outsourced work," the keywords are "process," "overseeing," "outsourced work."
        2.  **Scan the Knowledge Base:** Search the entire KNOWLEDGE BASE for sections, questions, or answers that contain these keywords or related concepts. The user's question phrasing might be different from the questions in the knowledge base, so you must search for concepts, not just exact text.
        3.  **Synthesize the Answer:** If you find one or more relevant pieces of information, combine them into a single, comprehensive, and well-formatted answer.
        4.  **Final Check & Fallback:** Read your synthesized answer. Does it directly address the user's question using only information from the knowledge base? 
            - If YES, provide that answer.
            - If NO, and you genuinely could not find any relevant information after following the steps above, then and ONLY then, you MUST respond with the exact phrase: "I don't have that specific information in our DDQ documents. Please contact our Compliance Officer, Peter Lau, at peterlau@wmcubehk.com or +852 3854 6419 for more details."

        【USER QUESTION】
        {question}

        【YOUR FINAL ANSWER】
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
    qa_dict = _parse_qa_from_kb()
    normalized_q = re.sub(r'[?.]$', '', question.lower().strip())

    if normalized_q in qa_dict:
        print(f"✅ Exact match found for: '{question}'")
        return qa_dict[normalized_q]
    else:
        print(f"⚠️ No exact match. Using AI for: '{question}'")
        return _get_gemini_semantic_response(question)
