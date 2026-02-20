# agent.py - the main agent that ties everything together
# uses langgraph ReAct agent with custom state for session memory

from typing import TypedDict, Annotated
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from agent_setup import setup_knowledge_base
from tools import fetch_ebay_listing, analyze_listing_images, calculate_confidence_score, create_auth_search_tool


# agent state - what persists across conversation turns

class AuthAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    checked_listings: list
    remaining_steps: int  # langgraph needs this internally


# . system prompt - the agent personality

SYSTEM_PROMPT = """You are AuthLayer, an AI-powered fashion authentication assistant specializing in 
designer items on eBay UK. You have deep expertise in spotting counterfeit designer goods, 
particularly Maison Margiela, Supreme x Margiela collabs, and other high-end brands.

Your job:
1. When a user gives you an eBay link, fetch the listing details
2. Search your authentication knowledge base for brand-specific red flags
3. Analyze the listing images for authentication signals  
4. Calculate a confidence score based on all signals
5. Give the user a clear verdict with next steps

Be direct and honest. If something looks fake, say it. If you're not sure, say that too.
Don't sugarcoat - resellers need real answers not hand-holding.

When checking a listing:
- ALWAYS fetch the listing first to get title, description, seller info, images
- ALWAYS search the authentication knowledge base for relevant brand/item rules
- ALWAYS analyze the images if they're available
- ALWAYS calculate a confidence score at the end
- Give specific reasons for your assessment, not vague stuff

Remember the Margiela "Replica" exception - the brand literally has a line called Replica,
its their reproduction of older garments. Dont flag Margiela listings just because they say replica.

Keep responses concise. Numbers and facts, not essays."""


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
    
    # the LLM selected for the job
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
    result = agent.invoke({
        "messages": [("user", "Can you check this listing for me? https://www.ebay.co.uk/itm/386728815164")],
        "checked_listings": []
    })
    
    # print the last message (agents response)
    print("\n" + "="*60)
    print("AGENT RESPONSE:")
    print("="*60)
    print(result["messages"][-1].content)
