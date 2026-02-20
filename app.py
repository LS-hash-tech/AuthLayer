# app.py - streamlit frontend for AuthLayer
# dark theme & clean, red accent, dust particles

import streamlit as st
import base64
from agent import create_auth_agent

# page config
st.set_page_config(
    page_title="AuthLayer",
    page_icon="A",
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

# custom css + dust particles + rotating text animation
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
    
    /* dust particles canvas */
    #dust-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 0;
    }
    
    /* make sure content sits above particles */
    .block-container {
        position: relative;
        z-index: 1;
        padding-top: 2rem;
        max-width: 900px;
    }
    
    /* header area */
    [data-testid="stHeader"] {
        background-color: #000000 !important;
        border-bottom: 1px solid #1a1a1a;
    }
    
    /* navbar */
    .navbar {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0 24px;
        border-bottom: 1px solid #1a1a1a;
        margin-bottom: 24px;
        position: relative;
        z-index: 2;
    }
    .navbar img {
        width: 36px;
        height: 36px;
        filter: brightness(1.1);
    }
    .navbar-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* hero card */
    .hero-card {
        background: linear-gradient(135deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%);
        border: 1px solid #1f1f1f;
        border-radius: 16px;
        padding: 48px 32px;
        text-align: center;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
        z-index: 2;
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
    .hero-badge {
        display: inline-block;
        background: rgba(220, 38, 38, 0.15);
        color: #dc2626;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    
    /* centered title + rotating word below */
    .hero-title-static {
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 3px;
        text-transform: uppercase;
        text-align: center;
        margin-bottom: 4px;
    }
    .hero-title-rotating {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #dc2626;
        height: 3rem;
        overflow: hidden;
        position: relative;
        text-align: center;
        margin-bottom: 16px;
    }
    .hero-title-rotating .word-slider {
        display: flex;
        flex-direction: column;
        align-items: center;
        animation: slideWords 21s ease-in-out infinite;
    }
    .hero-title-rotating .word-slider span {
        height: 3rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    @keyframes slideWords {
        0%, 14.28%      { transform: translateY(0); }
        16.66%, 30.95%  { transform: translateY(-3rem); }
        33.33%, 47.61%  { transform: translateY(-6rem); }
        50%, 64.28%     { transform: translateY(-9rem); }
        66.66%, 80.95%  { transform: translateY(-12rem); }
        83.33%, 97.61%  { transform: translateY(-15rem); }
        100%            { transform: translateY(0); }
    }
    
    .hero-subtitle {
        font-size: 0.95rem;
        color: #555;
        margin-bottom: 0;
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
        position: relative;
        z-index: 2;
    }
    .status-item {
        color: #555;
        font-size: 0.85rem;
    }
    .status-item span {
        color: #dc2626;
        font-weight: 600;
    }
    
    /* constrain chat input width to match content */
    [data-testid="stBottom"] {
        max-width: 900px;
        margin: 0 auto;
        left: 0;
        right: 0;
    }
    [data-testid="stBottom"] > div {
        max-width: 900px;
        margin: 0 auto;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* chat messages */
    [data-testid="stChatMessage"] {
        background-color: #0a0a0a !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-bottom: 8px !important;
    }
    
    /* chat input styling */
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
    
    /* confidence dashboard */
    .confidence-dashboard {
        background: linear-gradient(135deg, #0a0a0a 0%, #111 50%, #0a0a0a 100%);
        border: 1px solid #1f1f1f;
        border-radius: 16px;
        padding: 32px;
        margin: 16px 0;
        position: relative;
        overflow: hidden;
    }
    .confidence-dashboard::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--score-color, #dc2626), transparent);
    }
    .confidence-score-wrap {
        text-align: center;
        margin-bottom: 24px;
    }
    .confidence-label {
        font-size: 0.85rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }
    .confidence-number {
        font-size: 4.5rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 4px;
    }
    .confidence-level {
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .score-high { color: #4ade80; }
    .score-medium { color: #fbbf24; }
    .score-low { color: #f87171; }
    .score-vlow { color: #dc2626; }
    
    .confidence-divider {
        border: none;
        border-top: 1px solid #1f1f1f;
        margin: 20px 0;
    }
    .confidence-section-title {
        font-size: 0.8rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }
    .confidence-reason {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 8px;
        font-size: 0.9rem;
        color: #ccc;
    }
    .confidence-reason .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #dc2626;
        margin-top: 7px;
        flex-shrink: 0;
    }
    .confidence-next-step {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 8px;
        font-size: 0.9rem;
        color: #999;
    }
    .confidence-next-step .arrow {
        color: #dc2626;
        flex-shrink: 0;
        font-weight: 700;
    }
    
    /* hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
</style>

<!-- dust particles -->
<canvas id="dust-canvas"></canvas>
<script>
(function() {
    const canvas = document.getElementById('dust-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);
    
    const particles = [];
    const count = 60;
    
    for (let i = 0; i < count; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 1.5 + 0.5,
            speedX: (Math.random() - 0.5) * 0.3,
            speedY: (Math.random() - 0.5) * 0.2 - 0.1,
            opacity: Math.random() * 0.4 + 0.1,
            pulse: Math.random() * Math.PI * 2
        });
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(p => {
            p.x += p.speedX;
            p.y += p.speedY;
            p.pulse += 0.01;
            
            let currentOpacity = p.opacity + Math.sin(p.pulse) * 0.1;
            
            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;
            if (p.y < 0) p.y = canvas.height;
            if (p.y > canvas.height) p.y = 0;
            
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(220, 38, 38, ${currentOpacity})`;
            ctx.fill();
        });
        
        requestAnimationFrame(animate);
    }
    
    animate();
})();
</script>
""",
    unsafe_allow_html=True,
)

# top navbar with logo + name
if logo_b64:
    nav_logo = f'<img src="data:image/png;base64,{logo_b64}" alt="AuthLayer">'
else:
    nav_logo = '<span style="font-size:1.5rem;color:#dc2626;">A</span>'

st.markdown(
    f"""
<div class="navbar">
    {nav_logo}
    <span class="navbar-name">AuthLayer</span>
</div>
""",
    unsafe_allow_html=True,
)

# hero card with rotating words - centered
st.markdown(
    """
<div class="hero-card">
    <div class="hero-badge">AI Authentication</div>
    <div class="hero-title-static">AUTHENTICATE YOUR</div>
    <div class="hero-title-rotating">
        <div class="word-slider">
            <span>BAG</span>
            <span>SHOES</span>
            <span>JACKET</span>
            <span>BELT</span>
            <span>TROUSERS</span>
            <span>SHIRT</span>
        </div>
    </div>
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


def render_confidence_dashboard(response_text):
    """tries to parse confidence score from agent response and render a dashboard"""
    import re

    # look for score patterns in the response
    score_match = re.search(
        r'["\']?score["\']?\s*[:=]\s*(\d+)', response_text, re.IGNORECASE
    )
    if not score_match:
        score_match = re.search(
            r"confidence\s*(?:score)?\s*(?:of|:)\s*(\d+)", response_text, re.IGNORECASE
        )
    if not score_match:
        score_match = re.search(r"(\d+)\s*(?:%|percent)", response_text, re.IGNORECASE)

    if not score_match:
        return False

    score = int(score_match.group(1))
    score = min(max(score, 0), 100)

    # determine color class
    if score >= 85:
        color_class = "score-high"
        level = "LIKELY AUTHENTIC"
    elif score >= 60:
        color_class = "score-medium"
        level = "PROCEED WITH CAUTION"
    elif score >= 30:
        color_class = "score-low"
        level = "SIGNIFICANT RED FLAGS"
    else:
        color_class = "score-vlow"
        level = "ALMOST CERTAINLY FAKE"

    # extract reasons - look for bullet points or numbered items
    reasons = []
    reason_patterns = [
        re.findall(r"[-*]\s+(.+?)(?:\n|$)", response_text),
        re.findall(r"\d+\.\s+(.+?)(?:\n|$)", response_text),
    ]
    for matches in reason_patterns:
        for m in matches:
            cleaned = m.strip()
            if len(cleaned) > 10 and len(cleaned) < 200:
                reasons.append(cleaned)

    if not reasons:
        # fallback: split by sentences and grab relevant ones
        sentences = response_text.split(".")
        for s in sentences:
            s = s.strip()
            if any(
                word in s.lower()
                for word in [
                    "flag",
                    "concern",
                    "suspicious",
                    "fake",
                    "authentic",
                    "score",
                    "seller",
                    "label",
                    "stitch",
                ]
            ):
                if len(s) > 15 and len(s) < 200:
                    reasons.append(s)

    reasons = reasons[:6]  # cap at 6

    # build reasons html
    reasons_html = ""
    for r in reasons:
        reasons_html += f'<div class="confidence-reason"><div class="dot"></div><span>{r}</span></div>'

    if not reasons_html:
        reasons_html = '<div class="confidence-reason"><div class="dot"></div><span>See detailed analysis above</span></div>'

    # next steps based on score
    if score >= 85:
        steps = [
            "Item appears legitimate based on available signals",
            "Still recommended to inspect in person if possible",
            "Check return policy before purchasing",
        ]
    elif score >= 60:
        steps = [
            "Request additional photos (labels, tags, hardware closeups)",
            "Ask seller about provenance and where they got it",
            "Consider using a professional authentication service",
        ]
    else:
        steps = [
            "DO NOT purchase without professional authentication",
            "Multiple red flags detected - high risk of counterfeit",
            "Report listing if you believe it violates platform rules",
            "Look for the same item from a more reputable seller",
        ]

    steps_html = ""
    for s in steps:
        steps_html += f'<div class="confidence-next-step"><span class="arrow">></span><span>{s}</span></div>'

    dashboard_html = f"""
    <div class="confidence-dashboard">
        <div class="confidence-score-wrap">
            <div class="confidence-label">Confidence Score</div>
            <div class="confidence-number {color_class}">{score}</div>
            <div class="confidence-level {color_class}">{level}</div>
        </div>
        <hr class="confidence-divider">
        <div class="confidence-section-title">Why this score</div>
        {reasons_html}
        <hr class="confidence-divider">
        <div class="confidence-section-title">What to do next</div>
        {steps_html}
    </div>
    """

    st.markdown(dashboard_html, unsafe_allow_html=True)
    return True


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

                # show the text response
                st.markdown(response_text)

                # try to render confidence dashboard if score is in the response
                render_confidence_dashboard(response_text)

                st.session_state.messages.append({"role": "assistant", "content": response_text})

            except Exception as e:
                error_msg = f"something went wrong: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
