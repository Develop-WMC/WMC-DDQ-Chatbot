# file: llm.py

import google.generativeai as genai
import re

def _get_gemini_semantic_response(model, chat_history: list) -> str:
    """
    Gets a response from the Gemini model using the full conversation history.
    """
    try:
        # Convert Streamlit's chat history format to Gemini's format
        gemini_history = []
        for msg in chat_history:
            role = 'model' if msg['role'] == 'assistant' else 'user'
            gemini_history.append({'role': role, 'parts': [msg['content']]})

        # Start a chat session with the history
        chat = model.start_chat(history=gemini_history[:-1])
        
        # Send the last user message to get a response
        response = chat.send_message(gemini_history[-1]['parts'][0])
        
        if not response or not response.parts:
            block_reason = getattr(response, 'prompt_feedback', {}).get('block_reason', 'Unknown reason')
            return f"⚠️ Response was blocked: {block_reason}. Please rephrase your question."
        
        return response.text

    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg:
            return "⏱️ Request timed out. Please try again."
        elif "api key" in error_msg or "api_key" in error_msg:
            return "❌ API key error. Please check your Gemini API configuration."
        elif "quota" in error_msg or "limit" in error_msg:
            return "❌ API quota exceeded. Please try again later."
        return f"❌ An unexpected error occurred: {e}"

def get_response(question: str, chat_history: list, qa_dict: dict, model) -> str:
    """
    Provides an answer using a hybrid approach with conversation history.
    """
    normalized_q = re.sub(r'[?.,]$', '', question.lower().strip())

    # Exact match only works well for the first question in a session.
    if len(chat_history) <= 2 and normalized_q in qa_dict:
        print(f"✅ Exact match found for: '{question}'")
        return qa_dict[normalized_q]
    else:
        # For follow-up questions or semantic search, use the AI with full history
        print(f"⚠️ No exact match or it's a follow-up. Using AI with full history for: '{question}'")
        return _get_gemini_semantic_response(model, chat_history)
