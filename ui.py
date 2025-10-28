# file: ui.py

import streamlit as st
import json
from datetime import datetime
import html
import llm

# 可选：提供一个现代化的默认样式。如果你已有 css_content，可忽略这个常量。
DEFAULT_CSS = """
:root{
  --bg: radial-gradient(1200px 800px at 10% -10%, #e2f6ff, transparent 60%),
        radial-gradient(1200px 800px at 90% 110%, #ffe7fb, transparent 60%),
        linear-gradient(180deg, #f6f8fc, #eef2f8);
  --card: rgba(255,255,255,0.75);
  --elev: rgba(0,0,0,0.05);
  --border: rgba(0,0,0,0.08);
  --text: #1c2333;
  --muted: #5c6577;
  --primary: #3b82f6;
  --primary-600:#2563eb;
  --accent:#10b981;
  --danger:#ef4444;
  --radius: 14px;
}

html,body{height:100%}
body{
  background: var(--bg) fixed;
  color: var(--text);
}

/* 通用容器与卡片 */
.custom-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:14px 18px;margin-bottom:16px;
  border:1px solid var(--border);
  background:linear-gradient(180deg, rgba(255,255,255,0.6), rgba(255,255,255,0.35));
  -webkit-backdrop-filter: blur(10px);backdrop-filter: blur(10px);
  border-radius: calc(var(--radius) + 2px);
  box-shadow: 0 10px 30px var(--elev);
}
.company-name{
  font-weight:700;letter-spacing:.2px;display:flex;gap:10px;align-items:center;font-size:20px;
}
.company-tagline{color:var(--muted);font-size:14px}
.login-container,.chat-container,.metric-card,.contact-card,.success-box{
  border:1px solid var(--border);
  background: rgba(255,255,255,0.75);
  border-radius: var(--radius);
  box-shadow: 0 12px 28px var(--elev);
}

/* 登录 */
.login-container{padding:26px}
.login-title{font-size:20px;font-weight:700;margin-bottom:12px;display:flex;gap:8px;align-items:center}

/* 侧边栏小件 */
.metric-card{display:grid;gap:6px;padding:16px}
.metric-value{font-size:28px;font-weight:800}
.metric-label{color:var(--muted);font-size:13px}
.contact-card{display:grid;gap:8px;padding:16px}
.contact-name{font-weight:700}
.contact-info{font-family: ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}

/* 成功提示 */
.success-box{
  padding:10px 14px;font-weight:600;display:inline-flex;gap:8px;align-items:center;margin:8px 0;
  background: linear-gradient(180deg, #22c55e18, #22c55e0a);
  color:#16a34a;border-color:#22c55e55;
}

/* 聊天容器美化 */
.chat-container{
  padding:12px;
  background: linear-gradient(180deg,#ffffff90,#ffffff70);
}
.chat-container .stChatMessage{
  border:1px solid var(--border)!important;
  background: linear-gradient(180deg,#ffffff, #f7fafc)!important;
  border-radius: 16px!important;
  padding: 12px!important;
  box-shadow: 0 8px 20px var(--elev)!important;
  margin-bottom: 10px!important;
}

/* Streamlit 原生组件皮肤化（按钮、输入框） */
.stButton > button{
  border:1px solid var(--border);
  background: linear-gradient(135deg, var(--primary), var(--primary-600));
  color:white;border-radius:12px;padding:10px 14px;
  box-shadow: 0 8px 20px rgba(37,99,235,0.33);
}
.stButton > button:hover{filter:brightness(1.03)}
.stTextInput > div > div > input,
.stTextInput > div > div > input[type="password"]{
  border:1px solid var(--border);
  background:linear-gradient(180deg,#ffffff,#f9fafb);
  border-radius:12px;padding:12px 14px;
  box-shadow: inset 0 2px 6px rgba(0,0,0,0.04);
}

/* 分割线 */
hr, .stVerticalBlock{border-color: var(--border)!important}
"""

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

def _safe_html(text: str) -> str:
    """Basic HTML escape to reduce XSS risk when injecting into unsafe_allow_html blocks."""
    return html.escape(text or "")

def login_page(css_content: str = DEFAULT_CSS, model_name: str = "Model"):
    """Renders the professional login page for demo purposes."""
    load_css(css_content or DEFAULT_CSS)

    st.markdown("""
        <div class="custom-header">
            <div>
                <div class="company-name">🏢 Wealth Management Cube</div>
                <div class="company-tagline">Due Diligence Information Portal</div>
            </div>
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
        questions_asked = len([m for m in st.session_state.messages if m.get("role") == "user"]) if "messages" in st.session_state else 0

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

        if st.session_state.get("username") == "admin":
            st.markdown("---")
            st.markdown("### 🔧 Admin Tools")

            if st.button("📥 Download Conversation Logs", use_container_width=True):
                try:
                    with open("conversation_logs.jsonl", "r", encoding="utf-8") as f:
                        logs = f.read()
                    st.download_button("⬇️ Download Logs (JSONL)", logs, "conversation_logs.jsonl", "application/json", use_container_width=True)
                except FileNotFoundError:
                    st.warning("No logs available yet.")

def chat_page(css_content: str = DEFAULT_CSS, qa_dict: dict = None, model=None, model_name: str = "Model", temp: float = 0.2):
    """Renders the professional chat interface."""
    load_css(css_content or DEFAULT_CSS)
    _render_sidebar(model_name, temp)

    # Header section remains the same
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
            <div class="custom-header">
                <div>
                    <div class="company-name">💬 DDQ Assistant</div>
                    <div class="company-tagline">Ask me anything about WMC's Due Diligence</div>
                </div>
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

    username_safe = _safe_html(st.session_state.get("username", ""))
    st.markdown(f"""<div class="success-box">🟢 Logged in as: <strong>{username_safe}</strong></div>""", unsafe_allow_html=True)

    # Main chat area remains mostly the same
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    if not st.session_state.get("messages"):
        welcome_message = """👋 **Welcome to the WMC Due Diligence Portal!**

I can help you with questions about our company, compliance, IT, and more. I can also remember our conversation context for follow-up questions."""
        st.session_state.messages = [{"role": "assistant", "content": welcome_message}]

    for message in st.session_state.messages:
        with st.chat_message(message.get("role", "assistant"), avatar="🤖" if message.get("role") == "assistant" else "👤"):
            st.markdown(message.get("content", ""))

    if prompt := st.chat_input("💭 Type your question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Thinking..."):
                try:
                    response = llm.get_response(prompt, st.session_state.messages, qa_dict or {}, model)
                except Exception as e:
                    response = f"抱歉，生成回答时出现问题：{e}"
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        save_conversation_log(st.session_state.get("username") or "unknown", prompt, response)

    st.markdown('</div>', unsafe_allow_html=True)
