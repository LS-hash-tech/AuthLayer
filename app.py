# app.py - streamlit frontend for AuthLayer
# dark theme & clean, inspired by graby ai but with red accent

import streamlit as st
import base64
from agent import create_auth_agent

# page config
st.set_page_config(
    page_title="AuthLayer",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# load logo as base64
def get_logo_base64():
    try:
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


logo_b64 = get_logo_base64()

# custom css - dark theme, red accent, plain black bg
st.markdown(
    """
<style>
    /* kill all default streamlit bg */
    .stApp, .main, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stSidebar"], [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
    
    /* header area */
    [data-testid="stHeader"] {
        background-color: #000000 !important;
        border-bottom: 1px solid #1a1a1a;
    }
    
    /* main content area */
    .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }
    
    /* hero card */
    .hero-card {
        background: linear-gradient(135deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%);
        border: 1px solid #1f1f1f;
        border-radius: 16px;
        padding: 40px 32px;
        text-align: center;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #dc2626, transparent);
    }
    .hero-logo {
        width: 80px;
        height: 80px;
        margin: 0 auto 16px;
        filter: brightness(1.1);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 3px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #555;
        margin-bottom: 0;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(220, 38, 38, 0.15);
        color: #dc2626;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 16px;
        text-transform: uppercase;
    }
    
    /* status bar */
    .status-bar {
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 12px;
        padding: 16px 24px;
        display: flex;
        justify-content: center;
        gap: 32px;
        margin-bottom: 20px;
    }
    .status-item {
        color: #555;
        font-size: 0.85rem;
    }
    .status-item span {
        color: #dc2626;
        font-weight: 600;
    }
    
    /* chat messages */
    [data-testid="stChatMessage"] {
        background-color: #0a0a0a !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-bottom: 8px !important;
    }
    
    /* chat input */
    [data-testid="stChatInput"] {
        background-color: #0a0a0a !important;
        border-color: #1f1f1f !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: #0a0a0a !important;
        color: #e0e0e0 !important;
        border-color: #1f1f1f !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #444 !important;
    }
    
    /* buttons */
    .stButton > button {
        background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        transform: translateY(-1px) !important;
    }
    
    /* spinner */
    .stSpinner > div {
        border-top-color: #dc2626 !important;
    }
    
    /* sidebar */
    [data-testid="stSidebarContent"] {
        border-right: 1px solid #1a1a1a !important;
    }
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] li, [data-testid="stSidebar"] span {
        color: #999 !important;
    }
    
    /* scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #1f1f1f; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #333; }
    
    /* general text */
    p, span, li, h1, h2, h3, h4 { color: #e0e0e0; }
    
    /* hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
</style>
""",
    unsafe_allow_html=True,
)

# top navbar with logo + name
if logo_b64:
    nav_logo = f'<img src="data:image/png;base64,{logo_b64}" style="width:36px;height:36px;filter:brightness(1.1);" alt="AuthLayer">'
else:
    nav_logo = '<span style="font-size:1.5rem;">🔒</span>'

st.markdown(
    f"""
<div style="display:flex;align-items:center;gap:12px;padding:8px 0 24px;border-bottom:1px solid #1a1a1a;margin-bottom:24px;">
    {nav_logo}
    <span style="font-size:1.3rem;font-weight:700;color:#ffffff;letter-spacing:2px;text-transform:uppercase;">AuthLayer</span>
</div>
""",
    unsafe_allow_html=True,
)

# hero card
st.markdown(
    """
<div class="hero-card">
    <div class="hero-badge">AI Authentication</div>
    <div class="hero-title">AUTHENTICATE</div>
    <div class="hero-subtitle">Paste an eBay UK link. Get an instant authentication assessment.</div>
</div>
""",
    unsafe_allow_html=True,
)

# session state
if "agent" not in st.session_state:
    with st.spinner("loading knowledge base..."):
        st.session_state.agent = create_auth_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "checked_listings" not in st.session_state:
    st.session_state.checked_listings = []

# status bar
st.markdown(
    f"""
<div class="status-bar">
    <div class="status-item">Status: <span>Ready</span></div>
    <div class="status-item">Checked: <span>{len(st.session_state.checked_listings)}</span></div>
    <div class="status-item">Session: <span>Active</span></div>
</div>
""",
    unsafe_allow_html=True,
)

# sidebar
with st.sidebar:
    if logo_b64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_b64}" style="width:50px;margin-bottom:8px;">',
            unsafe_allow_html=True,
        )
    st.markdown("### AuthLayer")
    st.markdown(
        """
    **How to use:**
    1. Paste an eBay UK link
    2. Get authentication assessment
    3. Review score + reasoning
    
    **Brands covered:**
    - Maison Margiela
    - Supreme x Margiela
    - More soon
    """
    )

    st.markdown("---")

    if st.session_state.checked_listings:
        st.markdown("**Recent checks:**")
        for url in st.session_state.checked_listings[-5:]:
            st.markdown(f"- `{url[:45]}...`")

    st.markdown("---")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.checked_listings = []
        st.rerun()

# chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# chat input
if prompt := st.chat_input("paste an eBay link or ask about authentication..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # track ebay links
    if "ebay.co.uk/itm/" in prompt or "ebay.com/itm/" in prompt:
        words = prompt.split()
        for word in words:
            if "ebay" in word and "itm" in word:
                st.session_state.checked_listings.append(word)
                break

    # get response
    with st.chat_message("assistant"):
        with st.spinner("analyzing..."):
            try:
                agent_messages = []
                for msg in st.session_state.messages:
                    agent_messages.append((msg["role"], msg["content"]))

                result = st.session_state.agent.invoke(
                    {
                        "messages": agent_messages,
                        "checked_listings": st.session_state.checked_listings,
                        "remaining_steps": 25,
                    }
                )

                response_text = result["messages"][-1].content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

            except Exception as e:
                error_msg = f"something went wrong: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
