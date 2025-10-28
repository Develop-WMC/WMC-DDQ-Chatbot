# file: ui.py

import streamlit as st
import json
from datetime import datetime
import html
from pathlib import Path
import llm  # your existing module that provides get_response(prompt, messages, qa_dict, model)

# --- CSS loader --------------------------------------------------------------

FALLBACK_CSS = """
/* Minimal fallback in case style.css is missing */
* { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
.custom-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:#fff; padding: 1.25rem; border-radius: 12px; }
"""

def load_css(css_content: str | None = None):
    """Inject CSS. If style.css exists, inject it LAST so it wins the cascade."""
    # 1) Inject any inline CSS provided by caller (optional)
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

    # 2) Inject external style.css LAST (preferred)
    css_path = Path("style.css")
    if css_path.exists():
        raw = css_path.read_text(encoding="utf-8")
        # cache-buster comment so browsers pick up new styles after redeploys
        stamp = datetime.utcnow().isoformat() + "Z"
        st.markdown(f"<style>{raw}\n/* build:{stamp} */</style>", unsafe_allow_html=True)
    else:
        # 3) If no file, at least load a minimal fallback
        st.markdown(f"<style>{FALLBACK_CSS}</style>", unsafe_allow_html=True)

# --- Utilities ---------------------------------------------------------------

def save_conversation_log(username: str, question: str, answer: str):
    """Append one turn of conversation to a JSONL file."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "username": username,
        "question": question,
        "answer": answer,
    }
    try:
        with open("conversation_logs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except IOError as e:
        print(f"Warning: Could not write to log file. {e}")

def _safe_html(text: str) -> str:
    return html.escape(text or "")

def _ensure_session_defaults():
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("username", None)
    st.session_state.setdefault("messages", [])

# --- Sidebar -----------------------------------------------------------------

def _render_sidebar(model_name: str, temp: float):
    with st.sidebar:
        st.markdown("### 📊 Session Info")
        msgs = st.session_state.get("messages", [])
        questions_asked = len([m for m in msgs if m.get("role") == "user"])

        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{questions_asked}</div>
                <div class="metric-label">Questions Asked</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state["messages"] = []
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

        if st.session_state.get("username") == "admin":
            st.markdown("---")
            st.markdown("### 🔧 Admin Tools")
            if st.button("📥 Download Conversation Logs", use_container_width=True):
                try:
                    with open("conversation_logs.jsonl", "r", encoding="utf-8") as f:
                        logs = f.read()
                    st.download_button(
                        "⬇️ Download Logs (JSONL)",
                        logs,
                        "conversation_logs.jsonl",
                        "application/json",
                        use_container_width=True,
                    )
                except FileNotFoundError:
                    st.warning("No logs available yet.")

# --- Pages -------------------------------------------------------------------

def login_page(css_content: str | None = None, model_name: str = "Model"):
    """Render the login page (demo auth: any non-empty user/pass)."""
    _ensure_session_defaults()
    load_css(css_content)

    # Add a page-scoped root to let CSS detect "we are on login"
    st.markdown("<div id='login-root'></div>", unsafe_allow_html=True)

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
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.success("✅ Demo login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Please enter a username and password.")

        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("ℹ️ Demo Access Info"):
            st.info("In this demo mode, you can enter any non-empty username and password to log in.")

        st.caption(f"🔒 Secure connection • Powered by {model_name}")
        st.caption("UI css build: 2025-10-28")  # marker to confirm new build loads

def chat_page(
    css_content: str | None = None,
    qa_dict: dict | None = None,
    model=None,
    model_name: str = "Model",
    temp: float = 0.2,
):
    """Render the chat interface."""
    _ensure_session_defaults()
    load_css(css_content)
    _render_sidebar(model_name, temp)

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
            st.session_state.update({"authenticated": False, "username": None, "messages": []})
            st.rerun()

    username_safe = _safe_html(st.session_state.get("username") or "")
    st.markdown(f"""<div class="success-box">🟢 Logged in as: <strong>{username_safe}</strong></div>""", unsafe_allow_html=True)

    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Ensure messages list exists and has no empty entries (prevents empty white cards)
    msgs = st.session_state.get("messages", [])
    if not msgs:
        welcome_message = """👋 **Welcome to the WMC Due Diligence Portal!**

I can help you with questions about our company, compliance, IT, and more. I can also remember our conversation context for follow-up questions."""
        msgs = [{"role": "assistant", "content": welcome_message}]
    msgs = [m for m in msgs if str(m.get("content", "")).strip()]
    st.session_state["messages"] = msgs

    for message in st.session_state["messages"]:
        role = message.get("role", "assistant")
        with st.chat_message(role, avatar="🤖" if role == "assistant" else "👤"):
            st.markdown(message.get("content", ""))

    if prompt := st.chat_input("💭 Type your question here..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Thinking..."):
                try:
                    response = llm.get_response(prompt, st.session_state["messages"], qa_dict or {}, model)
                except Exception as e:
                    response = f"抱歉，生成回答时出现问题：{e}"
                st.markdown(response)

        st.session_state["messages"].append({"role": "assistant", "content": response})
        save_conversation_log(st.session_state.get("username") or "unknown", prompt, response)

    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("UI css build: 2025-10-28")  # marker to confirm new build loads
