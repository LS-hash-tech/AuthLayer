# tools.py - all the tools for the authentication agent
# ebay listing fetch, image analysis with reference comparison, knowledge base search, confidence scoring

import requests
import os
import base64
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()


# --- ebay stuff ---

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
    # strip query params (everything after ?) then grab item id from end
    clean_url = url.split("?")[0]
    return clean_url.split("/")[-1]


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


# --- load reference images for comparison ---


def load_reference_image(filename):
    """loads a reference image as base64 for sending to vision model"""
    try:
        # check a few possible locations
        paths = [
            filename,
            f"reference_images/{filename}",
            os.path.join(os.path.dirname(__file__), filename),
        ]
        for path in paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                # figure out media type
                if path.endswith(".webp"):
                    media = "image/webp"
                elif path.endswith(".png"):
                    media = "image/png"
                else:
                    media = "image/jpeg"
                return data, media
        return None, None
    except:
        return None, None


# --- image analysis with gpt-4o vision ---


@tool
def analyze_listing_images(
    image_urls: list, brand: str = "unknown", item_type: str = "unknown"
) -> str:
    """Analyzes listing images for authentication red flags using GPT-4o vision.
    Pass a list of image URLs from the eBay listing, the brand name, and item type (e.g. 'GAT sneakers', 'hoodie', 'wallet').
    For Margiela GATs this will compare against a known authentic reference image."""

    try:
        llm = ChatOpenAI(model="gpt-4o", max_tokens=2000)

        # check if we have a reference image for this item type
        has_reference = False
        ref_b64 = None
        ref_media = None

        brand_lower = brand.lower() if brand else ""
        item_lower = item_type.lower() if item_type else ""

        # load GAT reference if this is a margiela gat check
        if "margiela" in brand_lower and any(
            word in item_lower
            for word in ["gat", "replica", "sneaker", "trainer", "shoe"]
        ):
            ref_b64, ref_media = load_reference_image("reference_gat_authentic.webp")
            if ref_b64:
                has_reference = True

        # build the prompt
        if has_reference:
            prompt_text = f"""You are an expert fashion authenticator. You are checking {brand} {item_type}.

IMPORTANT: The FIRST image below is a KNOWN AUTHENTIC reference image. Compare ALL subsequent listing images against this reference.

For Margiela GATs specifically, focus on:
- HEEL TAB: On authentic, the heel tab is thin, flat, sits flush against the shoe. On fakes, it is puffy, overstuffed, and protrudes outward. THIS IS THE MOST IMPORTANT CHECK.
- Ankle collar: authentic is slim and structured, fake is bloated and rounded
- Overall back profile: authentic is sleek, fake is bulky
- Suede quality and texture
- Stitching precision
- Label placement and quality inside the shoe

Compare each listing image against the authentic reference and give a SPECIFIC verdict on whether the listed item matches the authentic or shows signs of being fake. Be direct - say "this looks authentic" or "this looks fake" with specific visual reasons."""
        else:
            prompt_text = f"""You are an expert fashion authenticator specializing in designer brands.
                
Analyze these listing images for the brand: {brand}, item type: {item_type}

Look for:
- Label/tag quality (stitching, font, alignment, material)
- Hardware quality (zippers, buttons, buckles)
- Material quality and texture
- Construction details (seams, stitching patterns)
- Any obvious red flags (wrong fonts, poor stitching, cheap materials)
- For Margiela: check heel tab on GATs, DWMZ marking on sweaters/knits, label attachment method
- For Supreme x Margiela: check label is sewn into seam not mounted on separate backing

Give your specific assessment. Be direct about whether each image looks authentic or fake and why."""

        # build message content
        content = [{"type": "text", "text": prompt_text}]

        # add reference image first if we have one
        if has_reference and ref_b64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{ref_media};base64,{ref_b64}"},
                }
            )

        # add listing images (max 4)
        for img_url in image_urls[:4]:
            content.append({"type": "image_url", "image_url": {"url": img_url}})

        message = HumanMessage(content=content)
        response = llm.invoke([message])

        return response.content

    except Exception as e:
        return f"image analysis failed: {str(e)}"


# --- knowledge base search (gets wired up in the agent) ---

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


# --- confidence scoring - images and knowledge base are primary, seller is secondary ---


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
    IMAGES and KNOWLEDGE BASE are the primary factors (worth most of the score).
    Seller feedback is secondary - a new seller alone should NOT tank the score.

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

    # --- PRIMARY SIGNALS (images + knowledge base) - these matter most ---

    # image analysis flags (up to -60 points)
    if image_analysis_summary and image_analysis_summary.lower() != "none":
        img_lower = image_analysis_summary.lower()

        # strong fake indicators from vision
        strong_fake_words = [
            "fake",
            "counterfeit",
            "not authentic",
            "replica fake",
            "definitely fake",
        ]
        for word in strong_fake_words:
            if word in img_lower:
                score -= 50
                reasons.append(
                    f"Image analysis indicates item is likely fake: '{word}' detected"
                )
                break

        # moderate concerns from vision
        moderate_words = [
            "suspicious",
            "concerning",
            "inconsistent",
            "poor quality",
            "red flag",
            "puffy",
            "overstuffed",
            "bloated",
        ]
        concern_count = 0
        for word in moderate_words:
            if word in img_lower:
                concern_count += 1
        if concern_count > 0:
            penalty = min(concern_count * 10, 40)
            score -= penalty
            reasons.append(f"Image analysis found {concern_count} visual concern(s)")

        # positive signals from vision (can recover some points)
        positive_words = [
            "authentic",
            "genuine",
            "looks real",
            "matches authentic",
            "correct",
            "proper",
        ]
        positive_count = 0
        for word in positive_words:
            if word in img_lower:
                positive_count += 1
        if positive_count >= 2 and concern_count == 0:
            score = min(score + 10, 100)
            reasons.append("Image analysis found multiple indicators of authenticity")

        # specific margiela checks
        if "dwmz" in img_lower:
            score -= 40
            reasons.append(
                "DWMZ marking detected - known fake indicator for Margiela knitwear"
            )
        if "heel tab" in img_lower and any(
            w in img_lower
            for w in ["puffy", "thick", "overstuffed", "bloated", "bulky"]
        ):
            score -= 40
            reasons.append(
                "Heel tab appears puffy/overstuffed - primary fake indicator for Margiela GATs"
            )

    # knowledge base match concerns (up to -30 points)
    if knowledge_base_matches and knowledge_base_matches.lower() != "none":
        kb_lower = knowledge_base_matches.lower()
        if any(
            w in kb_lower
            for w in ["dwmz", "puffy heel", "overstuffed", "patch on patch"]
        ):
            score -= 15
            reasons.append("Knowledge base flags match known counterfeit patterns")

    # --- SECONDARY SIGNALS (title, seller, reviews) ---

    # title/description keywords (up to -95 points - this is definitive)
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

    title_lower = title_flags.lower() if title_flags else ""
    for keyword in sus_keywords:
        if keyword in title_lower:
            # replica exception for margiela
            if (
                keyword == "rep"
                and "replica" in title_lower
                and "margiela" in title_lower
            ):
                reasons.append(
                    "'Replica' found but this is normal for Margiela Replica line - no penalty"
                )
                continue
            score = max(score - 95, 0)
            reasons.append(
                f"Suspicious keyword '{keyword}' found in title/description - almost certainly not authentic"
            )
            break

    # seller feedback (up to -20 points max - NOT the main factor)
    if seller_feedback_score == 0:
        score -= 15
        reasons.append(
            "Seller has 0 feedback - new account, exercise caution (but this alone doesnt mean fake)"
        )
    elif seller_feedback_score < 10:
        score -= 10
        reasons.append(
            f"Seller has low feedback count ({seller_feedback_score}) - relatively new account"
        )

    # feedback percentage (only penalize if really bad)
    try:
        fb_pct = float(seller_feedback_percentage)
        if fb_pct < 90:
            score -= 15
            reasons.append(f"Seller feedback percentage is concerning ({fb_pct}%)")
        elif fb_pct < 95:
            score -= 5
            reasons.append(f"Seller feedback percentage is below average ({fb_pct}%)")
    except:
        pass

    # review flags (up to -25 points)
    if review_flags and review_flags.lower() != "none":
        review_lower = review_flags.lower()
        for keyword in sus_keywords:
            if keyword in review_lower:
                score -= 25
                reasons.append(f"Buyer reviews mention '{keyword}' - concerning")
                break

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
            "Item appears legitimate based on available signals",
            "Still recommended to inspect in person if possible",
            "Check return policy before purchasing",
        ]
    elif score >= 60:
        next_steps = [
            "Request additional photos (labels, tags, hardware closeups)",
            "Ask seller about provenance and where they got it",
            "Consider using a professional authentication service",
            "Check sellers other listings for patterns",
        ]
    else:
        next_steps = [
            "DO NOT purchase without professional authentication",
            "Multiple red flags detected - high risk of counterfeit",
            "Report listing if you believe it violates platform rules",
            "Look for the same item from a more reputable seller",
        ]

    return {
        "score": score,
        "level": level,
        "reasons": reasons if reasons else ["no red flags detected"],
        "next_steps": next_steps,
    }


# quick test
if __name__ == "__main__":
    # test ebay fetch with long url
    result = fetch_ebay_listing.invoke(
        {
            "ebay_url": "https://www.ebay.co.uk/itm/389562275934?_skw=margiela&itmmeta=blah"
        }
    )
    print("listing title:", result.get("title", "error"))
    print("seller:", result.get("seller_username", "error"))
    print("images found:", len(result.get("images", [])))
