# file: ui.py

import streamlit as st
import json
from datetime import datetime
import llm

def load_css(css_content: str):
    """Inject custom CSS into the Streamlit app."""
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

def save_conversation_log(username: str, question: str, answer: str):
    # This function remains the same
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "question": question,
        "answer": answer
    }
    try:
        with open("conversation_logs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except IOError as e:
        print(f"Warning: Could not write to log file. {e}")

def login_page(css_content: str, model_name: str):
    """Renders the professional login page for demo purposes."""
    load_css(css_content)
    
    st.markdown("""
        <div class="custom-header">
            <div class="company-name">🏢 Wealth Management Cube</div>
            <div class="company-tagline">Due Diligence Information Portal</div>
        </div>
    """, unsafe_allow_html=True)
    
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🔐 Secure Login (Demo)</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter any username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter any password", key="login_pass")
            
            if st.form_submit_button("🔓 Login", use_container_width=True):
                if username and password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Demo login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Please enter a username and password.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("ℹ️ Demo Access Info"):
            st.info("In this demo mode, you can enter any non-empty username and password to log in.")
        
        st.caption(f"🔒 Secure connection • Powered by {model_name}")

def _render_sidebar(model_name: str, temp: float):
    # This function remains mostly the same
    with st.sidebar:
        st.markdown("### 📊 Session Info")
        questions_asked = len([m for m in st.session_state.messages if m["role"] == "user"])
        
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{questions_asked}</div>
                <div class="metric-label">Questions Asked</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📞 Contact")
        st.markdown("""
            <div class="contact-card">
                <div class="contact-name">Lau Hiu Fung Peter</div>
                <div style="color: #888; font-size: 0.9rem;">Compliance Officer</div>
                <div class="contact-info">📧 peterlau@wmcubehk.com</div>
                <div class="contact-info">📱 +852 3854 6419</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### ℹ️ About This Tool")
        st.info(f"""
            This AI assistant uses a hybrid search on WMC's official DDQ documents.
            🤖 Model: {model_name}
            🌡️ Temp: {temp}
        """)
        
        if st.session_state.username == "admin":
            st.markdown("---")
            st.markdown("### 🔧 Admin Tools")
            
            if st.button("📥 Download Conversation Logs", use_container_width=True):
                try:
                    with open("conversation_logs.jsonl", "r", encoding="utf-8") as f:
                        logs = f.read()
                    st.download_button("⬇️ Download Logs (JSONL)", logs, "conversation_logs.jsonl", "application/json", use_container_width=True)
                except FileNotFoundError:
                    st.warning("No logs available yet.")

def chat_page(css_content: str, qa_dict: dict, model, model_name: str, temp: float):
    """Renders the professional chat interface."""
    load_css(css_content)
    _render_sidebar(model_name, temp)

    # Header section remains the same
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
            <div class="custom-header">
                <div class="company-name">💬 DDQ Assistant</div>
                <div class="company-tagline">Ask me anything about WMC's Due Diligence</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.write("")
        st.write("")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()

    st.markdown(f"""<div class="success-box">🟢 Logged in as: <strong>{st.session_state.username}</strong></div>""", unsafe_allow_html=True)

    # Main chat area remains mostly the same
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        welcome_message = """👋 **Welcome to the WMC Due Diligence Portal!**

I can help you with questions about our company, compliance, IT, and more. I can also remember our conversation context for follow-up questions."""
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("💭 Type your question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Thinking..."):
                response = llm.get_response(prompt, st.session_state.messages, qa_dict, model)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_conversation_log(st.session_state.username, prompt, response)
    
    st.markdown('</div>', unsafe_allow_html=True)
