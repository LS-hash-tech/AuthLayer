# all the tools for the authentication agent
# + ebay listing fetch, image analysis, knowledge base search, confidence scoring

import requests
import os
import base64
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()


#    ebay

def get_ebay_token():
    # posts credentials to ebay, gets back an access token
    app_id = os.getenv("EBAY_APP_ID")
    cert_id = os.getenv("EBAY_CERT_ID")

    url = "https://api.ebay.com/identity/v1/oauth2/token"

    response = requests.post(
        url,
        auth=(app_id, cert_id),
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
    )

    token = response.json()["access_token"]
    return token


def get_id_from_url(url):
    # grabs the item id from the end of an ebay link
    return url.split("/")[-1]


@tool
def fetch_ebay_listing(ebay_url: str) -> dict:
    """Fetches an eBay listing's details including title, description, condition, images, and seller info.
    Takes a full eBay URL like https://www.ebay.co.uk/itm/123456789"""

    try:
        item_id = get_id_from_url(ebay_url)
        token = get_ebay_token()

        url = f"https://api.ebay.com/buy/browse/v1/item/v1|{item_id}|0"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB",
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        # pull out just the fields we actually need for authentication
        listing = {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "condition": data.get("condition", ""),
            "price": data.get("price", {}),
            "seller_username": data.get("seller", {}).get("username", ""),
            "feedback_score": data.get("seller", {}).get("feedbackScore", 0),
            "feedback_percentage": data.get("seller", {}).get(
                "feedbackPercentage", "0"
            ),
            "images": [
                img.get("imageUrl", "") for img in data.get("additionalImages", [])
            ],
            "main_image": data.get("image", {}).get("imageUrl", ""),
            "item_url": ebay_url,
        }

        # add the main image to the front of the images list
        if listing["main_image"]:
            listing["images"].insert(0, listing["main_image"])

        return listing

    except Exception as e:
        return {"error": f"couldnt fetch listing: {str(e)}"}


# ...... image analysis with gpt-4o vision


@tool
def analyze_listing_images(image_urls: list, brand: str = "unknown") -> str:
    """Analyzes listing images for authentication red flags using GPT-4o vision.
    Pass a list of image URLs from the eBay listing and the brand name."""

    try:
        llm = ChatOpenAI(model="gpt-4o", max_tokens=1500)

        # build the message with images
        content = [
            {
                "type": "text",
                "text": f"""You are an expert fashion authenticator specializing in designer brands.
                
Analyze these listing images for the brand: {brand}

Look for:
- Label/tag quality (stitching, font, alignment, material)
- Hardware quality (zippers, buttons, buckles)
- Material quality and texture
- Construction details (seams, stitching patterns)
- Any obvious red flags (wrong fonts, poor stitching, cheap materials)
- For Margiela specifically: check heel tab on GATs, DWMZ marking on sweaters/knits, label attachment method

Give your assessment of each image and note any red flags.
Be specific about what you see, not vague.""",
            }
        ]

        # add each image to the message (max 4 to save tokens)
        for img_url in image_urls[:4]:
            content.append({"type": "image_url", "image_url": {"url": img_url}})

        message = HumanMessage(content=content)
        response = llm.invoke([message])

        return response.content

    except Exception as e:
        return f"image analysis failed: {str(e)}"


#    knowledge base search (gets wired up in the agent)


def create_auth_search_tool(vectorstore):
    """creates the RAG search tool using the vectorstore from agent_setup"""

    @tool
    def search_authentication_guide(query: str) -> str:
        """Searches the authentication knowledge base for brand-specific authentication tips,
        red flags, and fake vs real comparisons. Use this when you need to look up how to
        authenticate a specific brand or item type."""

        results = vectorstore.similarity_search(query, k=3)

        if not results:
            return "nothing found in the knowledge base for that query"

        # combine the top results
        combined = ""
        for i, doc in enumerate(results):
            combined += f"\n--- Source: {doc.metadata.get('source', 'unknown')} ---\n"
            combined += doc.page_content + "\n"

        return combined

    return search_authentication_guide


#   confidence scoring


@tool
def calculate_confidence_score(
    title_flags: str = "none",
    seller_feedback_score: int = 0,
    seller_feedback_percentage: str = "0",
    review_flags: str = "none",
    image_analysis_summary: str = "none",
    knowledge_base_matches: str = "none",
) -> dict:
    """Calculates an authentication confidence score based on all available signals.

    Args:
        title_flags: any suspicious keywords found in title/description
        seller_feedback_score: sellers total number of feedbacks
        seller_feedback_percentage: sellers positive feedback %
        review_flags: any concerning keywords in seller reviews
        image_analysis_summary: summary of what the image analysis found
        knowledge_base_matches: relevant authentication rules from knowledge base
    """

    score = 100  # start at 100% authentic
    reasons = []

    # check title/description for dodgy keywords
    sus_keywords = [
        "fake",
        "not real",
        "dupe",
        "dup",
        "copycat",
        "not authentic",
        "non-authentic",
        "counterfeit",
        "imitation",
        "rep",
        "knockoff",
        "not auth",
    ]

    title_lower = title_flags.lower()
    for keyword in sus_keywords:
        if keyword in title_lower:
            # replica is an exception for margiela
            if (
                keyword == "rep"
                and "replica" in title_lower
                and "margiela" in title_lower.lower()
            ):
                reasons.append(
                    "'replica' found but this is normal for Margiela Replica line - no penalty"
                )
                continue
            score = max(score - 95, 0)  # basically kills it
            reasons.append(f"suspicious keyword '{keyword}' found in title/description")
            break

    # seller feedback check
    if seller_feedback_score == 0:
        score -= 40
        reasons.append("seller has 0 feedback - major red flag")
    elif seller_feedback_score < 10:
        score -= 25
        reasons.append(
            f"seller only has {seller_feedback_score} feedbacks - new account"
        )
    elif seller_feedback_score < 50:
        score -= 10
        reasons.append(f"seller has low feedback count ({seller_feedback_score})")

    # feedback percentage
    try:
        fb_pct = float(seller_feedback_percentage)
        if fb_pct < 95:
            score -= 20
            reasons.append(f"seller feedback percentage is low ({fb_pct}%)")
        elif fb_pct < 98:
            score -= 5
            reasons.append(
                f"seller feedback percentage is decent but not great ({fb_pct}%)"
            )
    except:
        pass

    # review flags
    if review_flags and review_flags.lower() != "none":
        review_lower = review_flags.lower()
        for keyword in sus_keywords:
            if keyword in review_lower:
                score -= 30
                reasons.append(f"buyer reviews mention '{keyword}' - concerning")
                break

    # image analysis flags
    if image_analysis_summary and image_analysis_summary.lower() != "none":
        img_lower = image_analysis_summary.lower()
        red_flag_words = [
            "fake",
            "counterfeit",
            "suspicious",
            "poor quality",
            "inconsistent",
            "red flag",
            "concerning",
            "dwmz",
        ]
        for word in red_flag_words:
            if word in img_lower:
                score -= 15
                reasons.append(f"image analysis flagged: {word}")

    score = max(score, 0)  # dont go below 0

    # confidence level
    if score >= 85:
        level = "HIGH - likely authentic"
    elif score >= 60:
        level = "MEDIUM - some concerns, proceed with caution"
    elif score >= 30:
        level = "LOW - significant red flags detected"
    else:
        level = "VERY LOW - almost certainly not authentic"

    # next steps based on score
    if score >= 85:
        next_steps = [
            "item appears legitimate based on available signals",
            "still recommended to inspect in person if possible",
            "check return policy before purchasing",
        ]
    elif score >= 60:
        next_steps = [
            "request additional photos (labels, tags, hardware closeups)",
            "ask seller about provenance/where they got it",
            "consider using a professional authentication service",
            "check sellers other listings for patterns",
        ]
    else:
        next_steps = [
            "DO NOT purchase without professional authentication",
            "multiple red flags detected - high risk of counterfeit",
            "report listing if you believe it violates platform rules",
            "look for the same item from a more reputable seller",
        ]

    return {
        "score": score,
        "level": level,
        "reasons": reasons if reasons else ["no red flags detected"],
        "next_steps": next_steps,
    }


# quick test
if __name__ == "__main__":
    # test ebay fetch
    result = fetch_ebay_listing.invoke(
        {"ebay_url": "https://www.ebay.co.uk/itm/386728815164"}
    )
    print("listing title:", result.get("title", "error"))
    print("seller:", result.get("seller_username", "error"))
    print("images found:", len(result.get("images", [])))
