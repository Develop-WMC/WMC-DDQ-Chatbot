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
            
        # --- UPDATED: Add system instruction during initialization ---
        system_instruction = f"""You are a world-class Due Diligence Assistant for Wealth Management Cube Limited (WMC). Your task is to answer user questions based ONLY on the provided knowledge base.

        【KNOWLEDGE BASE - START】
        {config.KNOWLEDGE_BASE}
        【KNOWLEDGE BASE - END】

        【CRITICAL RULES】
        1.  Analyze the user's latest question in the context of the entire conversation history.
        2.  Your answer MUST be based ONLY on the information found in the KNOWLEDGE BASE. Do not use any external knowledge.
        3.  If the answer to the user's question is explicitly stated in the knowledge base (e.g., "periodically"), provide that answer first. If the user asks for more specific details that are not available (e.g., asking for a specific number of months when the text only says "periodically"), then you MUST state that the specific detail is not available.
        4.  If you genuinely cannot find any relevant information for the user's question in the knowledge base, then and ONLY then, respond with the exact phrase: "I don't have that specific information in our DDQ documents. Please contact our Compliance Officer, Peter Lau, at peterlau@wmcubehk.com or +852 3854 6419 for more details."
        """
        
        model = genai.GenerativeModel(
            model_name=config.MODEL_NAME,
            generation_config=config.GENERATION_CONFIG,
            safety_settings=config.SAFETY_SETTINGS,
            system_instruction=system_instruction # <-- Pass instructions here
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
            normalized_question = re.sub(r'[?.,]$', '', question.lower().strip())
            qa_dict[normalized_question] = answer
            
    return qa_dict

def _get_gemini_semantic_response(chat_history: list) -> str:
    """
    Gets a response from the Gemini model using the full conversation history.
    """
    try:
        model = initialize_model()
        if not model:
            return "Error: Model initialization failed. Please check your API key."

        # Convert Streamlit's chat history format to Gemini's format
        # Gemini expects 'role' to be 'user' or 'model'
        gemini_history = []
        for msg in chat_history:
            role = 'model' if msg['role'] == 'assistant' else 'user'
            gemini_history.append({'role': role, 'parts': [msg['content']]})

        # Start a chat session with the history
        chat = model.start_chat(history=gemini_history[:-1]) # History excluding the last user message
        
        # Send the last user message to get a response
        response = chat.send_message(gemini_history[-1]['parts'][0])
        
        if not response or not response.parts:
            block_reason = getattr(response, 'prompt_feedback', {}).get('block_reason', 'Unknown reason')
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

def get_response(question: str, chat_history: list) -> str:
    """
    Provides an answer using a hybrid approach:
    1. Tries to find an exact match for the current question.
    2. If no exact match, falls back to the AI with the full chat history.
    """
    qa_dict = _parse_qa_from_kb()
    normalized_q = re.sub(r'[?.,]$', '', question.lower().strip())

    # Exact match only works for non-contextual, full questions
    if normalized_q in qa_dict:
        print(f"✅ Exact match found for: '{question}'")
        return qa_dict[normalized_q]
    else:
        # For follow-up questions or semantic search, use the AI with full history
        print(f"⚠️ No exact match. Using AI with full history for: '{question}'")
        return _get_gemini_semantic_response(chat_history)
