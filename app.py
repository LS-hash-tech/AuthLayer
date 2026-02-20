# app.py.. streamlit frontend for AuthLayer
# dark theme & clean

import streamlit as st
from agent import create_auth_agent

# page config
st.set_page_config(
    page_title="AuthLayer",
    page_icon="🔍",
    layout="wide"
)

# dark styling
st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; }
    .main-title { 
        font-size: 2.5rem; 
        font-weight: 700; 
        color: #ffffff;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .score-high { color: #4ade80; font-size: 2rem; font-weight: 700; }
    .score-medium { color: #fbbf24; font-size: 2rem; font-weight: 700; }
    .score-low { color: #f87171; font-size: 2rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# header
st.markdown('<p class="main-title">🔍 AuthLayer</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-powered authentication for designer fashion on eBay UK</p>', unsafe_allow_html=True)

# session state - keeps track of stuff between reruns
if "agent" not in st.session_state:
    with st.spinner("loading authentication knowledge base..."):
        st.session_state.agent = create_auth_agent()
    st.success("ready to authenticate")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "checked_listings" not in st.session_state:
    st.session_state.checked_listings = []

# sidebar - quick info
with st.sidebar:
    st.markdown("### How to use")
    st.markdown("""
    1. Paste an eBay UK listing URL
    2. Ask about any designer item
    3. Get an authentication assessment
    
    **Supported brands:**
    - Maison Margiela (GATs, Tabis, knitwear)
    - Supreme x Margiela collabs
    - More coming soon
    """)
    
    st.markdown("---")
    st.markdown(f"**Listings checked this session:** {len(st.session_state.checked_listings)}")
    
    if st.session_state.checked_listings:
        st.markdown("**Recent checks:**")
        for url in st.session_state.checked_listings[-5:]:
            st.markdown(f"- {url[:50]}...")
    
    st.markdown("---")
    if st.button("clear chat"):
        st.session_state.messages = []
        st.session_state.checked_listings = []
        st.rerun()

# show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# chat input
if prompt := st.chat_input("paste an eBay link or ask about authentication..."):
    
    # add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # track if they pasted a link
    if "ebay.co.uk/itm/" in prompt or "ebay.com/itm/" in prompt:
        # extract url from the message
        words = prompt.split()
        for word in words:
            if "ebay" in word and "itm" in word:
                st.session_state.checked_listings.append(word)
                break
    
    # get agent response
    with st.chat_message("assistant"):
        with st.spinner("analyzing..."):
            try:
                # build the full message history for the agent
                agent_messages = []
                for msg in st.session_state.messages:
                    agent_messages.append((msg["role"], msg["content"]))
                
                result = st.session_state.agent.invoke({
                    "messages": agent_messages,
                    "checked_listings": st.session_state.checked_listings,
                })
                
                # get the agents response
                response_text = result["messages"][-1].content
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
            except Exception as e:
                error_msg = f"something went wrong: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})