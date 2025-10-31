# file: app.py

import streamlit as st
import google.generativeai as genai
import os
from utils import parse_uploaded_file # We assume utils.py is now correct

# --- Page Configuration ---
st.set_page_config(
    page_title="WMC Due Diligence Chatbot",
    page_icon="🤖",
    layout="wide"
)

# --- Main App Logic ---
def main():
    """
    Main function to run the Streamlit chatbot application.
    """
    st.title("WMC Due Diligence Chatbot 📝")
    st.write("Upload your due diligence documents (PDF, DOCX, XLSX) and ask questions.")

    # --- Sidebar for API Key and File Upload ---
    with st.sidebar:
        st.header("Configuration")

        # API Key Management using Streamlit Secrets for deployment
        # or manual input for local development.
        if 'GOOGLE_API_KEY' in st.secrets:
            api_key = st.secrets['GOOGLE_API_KEY']
            st.success("API key found in secrets.", icon="✅")
        else:
            api_key = st.text_input("Enter your Google API Key:", type="password")
            if api_key:
                st.success("API key entered.", icon="🔑")

        # File Uploader Widget
        st.header("Document Upload")
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=["pdf", "docx", "xlsx"],
            help="Supports PDF, Word (DOCX), and Excel (XLSX) files."
        )

    # --- Initial Checks ---
    # Stop the app if the API key is not provided.
    if not api_key:
        st.warning("Please enter your Google API Key in the sidebar to proceed.")
        st.stop()

    # Configure the generative model.
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Error configuring the generative model: {e}")
        st.stop()

    # --- Session State Initialization ---
    # Initialize chat history if it doesn't exist.
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your Due Diligence Chatbot. Upload a document and I can answer your questions about it."}
        ]
    # Initialize keys for tracking the uploaded file and its content.
    if "uploaded_file_id" not in st.session_state:
        st.session_state.uploaded_file_id = None
    if "document_text" not in st.session_state:
        st.session_state.document_text = None

    # --- CORRECTED: File Processing and State Management ---
    # This block robustly handles file addition, removal, and replacement.
    
    # Safely get the ID of the current file, or None if no file is uploaded.
    # getattr(object, 'attribute', default) prevents an AttributeError.
    current_file_id = getattr(uploaded_file, 'id', None)

    # Check if the file has changed.
    if st.session_state.uploaded_file_id != current_file_id:
        # Update the file ID in the session state.
        st.session_state.uploaded_file_id = current_file_id

        if uploaded_file is not None:
            # A new file has been uploaded or an existing one was replaced.
            st.session_state.document_text = parse_uploaded_file(uploaded_file)
            # Reset chat history because the document context has changed.
            st.session_state.messages = [
                {"role": "assistant", "content": f"Document '{uploaded_file.name}' has been loaded. How can I help you?"}
            ]
            st.toast(f"✅ Successfully parsed '{uploaded_file.name}'")
            st.rerun() # Rerun the script to immediately reflect the changes in the UI.
        else:
            # The file has been removed by the user.
            st.session_state.document_text = None
            # Reset chat history as the context is now gone.
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am your Due Diligence Chatbot. Upload a document and I can answer your questions about it."}
            ]
            st.toast("ℹ️ Document removed. Chat has been reset.")
            st.rerun() # Rerun to update the UI.

    # --- Display Chat History ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Handle User Input ---
    if prompt := st.chat_input("Ask a question about the document..."):
        # Add user message to chat history and display it.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Check if a document is uploaded before attempting to answer.
        if st.session_state.document_text is None:
            with st.chat_message("assistant"):
                st.warning("Please upload a document before asking questions.")
            st.stop()

        # Prepare the prompt for the language model.
        with st.spinner("Thinking..."):
            try:
                full_prompt = f"""
                You are a helpful assistant specialized in analyzing due diligence documents.
                Based on the following document content, please answer the user's question.

                DOCUMENT CONTENT:
                ---
                {st.session_state.document_text}
                ---

                USER'S QUESTION:
                {prompt}
                """
                response = model.generate_content(full_prompt)
                assistant_response = response.text

            except Exception as e:
                assistant_response = f"An error occurred while generating the response: {e}"

        # Add assistant response to chat history and display it.
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        with st.chat_message("assistant"):
            st.markdown(assistant_response)


if __name__ == "__main__":
    main()
