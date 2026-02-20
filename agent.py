# agent.py - the main agent that ties everything together
# uses langgraph ReAct agent with custom state for session memory

from typing import TypedDict, Annotated
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from agent_setup import setup_knowledge_base
from tools import fetch_ebay_listing, analyze_listing_images, calculate_confidence_score, create_auth_search_tool


# --- agent state - what persists across conversation turns ---

class AuthAgentState(TypedDict):
    messages: Annotated[list, add_messages]  # conversation history
    checked_listings: list  # tracks what listings the user already checked this session
    remaining_steps: int  # langgraph needs this internally


# --- system prompt - the agent personality ---

SYSTEM_PROMPT = """You are AuthLayer, an AI-powered fashion authentication assistant specializing in 
designer items on eBay UK. You have deep expertise in spotting counterfeit designer goods, 
particularly Maison Margiela, Supreme x Margiela collabs, and other high-end brands.

CRITICAL RULES FOR EVERY LISTING CHECK:
You MUST use ALL 4 tools in this exact order for every eBay link:
1. fetch_ebay_listing - get the listing data
2. search_authentication_guide - search knowledge base for brand-specific rules
3. analyze_listing_images - send images to vision model for analysis
4. calculate_confidence_score - calculate final score based on ALL signals

NEVER skip a tool. NEVER give a verdict without using all 4.

When presenting results, ALWAYS format your response like this:

## Authentication Report

**Item:** [item title]
**Seller:** [username] | Feedback: [score] ([percentage]%)

### Analysis

[Your detailed analysis covering listing data, knowledge base matches, and image analysis findings]

### Confidence Score: [NUMBER]

**Here is why:**
- [reason 1]
- [reason 2]
- [reason 3]
- [etc]

### What To Do Next
- [action 1]
- [action 2]
- [action 3]

---

Be direct and honest. If something looks fake, say it. If you are not sure, say that too.
Do not sugarcoat - resellers need real answers not hand-holding.

Remember the Margiela "Replica" exception - the brand literally has a line called Replica,
its their reproduction of older garments. Do not flag Margiela listings just because they say replica.

Keep analysis sections concise. Numbers and facts, not essays."""


def create_auth_agent():
    # setup the knowledge base (loads md files, chunks, embeds, stores)
    print("setting up knowledge base...")
    vectorstore = setup_knowledge_base()

    # create the RAG search tool using our vectorstore
    auth_search = create_auth_search_tool(vectorstore)

    # all the tools the agent can use
    tools = [
        fetch_ebay_listing,
        analyze_listing_images,
        auth_search,
        calculate_confidence_score,
    ]

    # the brain
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # wire it all together
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_schema=AuthAgentState,
        prompt=SYSTEM_PROMPT,
    )

    return agent


# test it if running directly
if __name__ == "__main__":
    agent = create_auth_agent()

    # test with a real listing
    result = agent.invoke(
        {
            "messages": [
                (
                    "user",
                    "Can you check this listing for me? https://www.ebay.co.uk/itm/386728815164",
                )
            ],
            "checked_listings": [],
            "remaining_steps": 25,
        }
    )

    # print the last message (agents response)
    print("\n" + "="*60)
    print("AGENT RESPONSE:")
    print("="*60)
    print(result["messages"][-1].content)
