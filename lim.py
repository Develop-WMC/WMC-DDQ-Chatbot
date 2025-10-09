import streamlit as st
import google.generativeai as genai
import config  # Import our configuration module

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

def get_gemini_response(question: str) -> str:
    """
    Get response from Gemini API with strict anti-hallucination measures.
    """
    try:
        model = initialize_model()
        if not model:
            return "Error: Model initialization failed. Please check your API key."
        
        # This strict prompt is crucial for preventing the model from using outside knowledge.
        prompt = f"""You are a Due Diligence Assistant for Wealth Management Cube Limited (WMC), a Hong Kong SFC-licensed fund platform.

        【CRITICAL RULES - YOU MUST FOLLOW STRICTLY】
        1. ❌ You can ONLY use information from the KNOWLEDGE BASE below.
        2. ❌ You CANNOT make up, guess, assume, or use any external knowledge.
        3. ❌ If the information is NOT in the KNOWLEDGE BASE, you MUST say exactly: "I don't have that specific information in our DDQ documents. Please contact our Compliance Officer, Peter Lau, at peterlau@wmcubehk.com or +852 3854 6419 for more details."
        4. ✅ Be professional, concise, and accurate.
        5. ✅ Include relevant details (dates, numbers, names) when available in the documents.
        6. ✅ Quote directly from the documents when possible.
        7. ❌ Never say things like "based on industry standards" or "typically" or "probably" - only use what's in the documents.

        【KNOWLEDGE BASE - START】
        {config.KNOWLEDGE_BASE}
        【KNOWLEDGE BASE - END】

        【USER QUESTION】
        {question}

        【YOUR ANSWER】
        (Answer based ONLY on the KNOWLEDGE BASE above. If the information is not found, use the "I don't have that information" template provided in rule 3.)
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
