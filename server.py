"""
Flask REST API backend for Mini Semrush toolkit.
Run: flask --app server run -p 5001
"""
import os
from urllib.parse import urlparse

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import textstat
from google import genai as newgenai
from google.genai import types as genai_types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERP_API_KEY = os.getenv("SERPAPI_KEY", "4f217e661e2152844acd05cf7f500032d061f8af759968b4f36bc9e278b5d5cb")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyA5j9ZkjKW50P7QVuT1zxiWdaGRgun4FpQ")
GEMINI_NEW_KEY = os.getenv("GEMINI_NEW_KEY")

client_new = newgenai.Client(api_key=GEMINI_NEW_KEY) if GEMINI_NEW_KEY else None
# For AI Visibility we use the same client (gemini-2.5-flash)
client_visibility = newgenai.Client(api_key=os.getenv("GEMINI_API_KEY") or GEMINI_NEW_KEY) if (os.getenv("GEMINI_API_KEY") or GEMINI_NEW_KEY) else None

# Gemini client for chatbot (prefer GEMINI_API_KEY, fallback to GEMINI_NEW_KEY)
_chatbot_api_key = os.getenv("GEMINI_API_KEY") or GEMINI_NEW_KEY
client_chatbot = newgenai.Client(api_key=_chatbot_api_key) if _chatbot_api_key else None

app = Flask(__name__)
# Allow all origins in dev so browser always gets CORS headers (fixes "Failed to fetch")
CORS(app, origins=["*"], allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "OPTIONS"], supports_credentials=False)


@app.after_request
def add_cors_headers(response):
    """Ensure CORS is on every response so browser never blocks."""
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# ============ Chatbot: Gemini function declarations ============
def _schema_obj(properties, required=None):
    """Build a Schema for type=object with given properties and required list."""
    return genai_types.Schema(type=genai_types.Type.OBJECT, properties=properties, required=required or [])


CHATBOT_FUNCTION_DECLARATIONS = [
    genai_types.FunctionDeclaration(
        name="ai_visibility_analyze",
        description="Analyze AI visibility: how visible a brand is for a keyword in Google search and in AI answers. Use when the user asks about brand visibility, AI visibility, or ranking for a keyword.",
        parameters=_schema_obj(
            {"brand_name": genai_types.Schema(type=genai_types.Type.STRING, description="Brand or company name"),
             "keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Search keyword")},
            ["brand_name", "keyword"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="ppc_ads",
        description="Get PPC/product ads for a keyword. Use when the user asks about ads, paid results, or product ads for a keyword.",
        parameters=_schema_obj(
            {"keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Search keyword")},
            ["keyword"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="ppc_calculator",
        description="Estimate PPC campaign metrics: clicks, conversions, revenue, profit. Use when the user asks for PPC ROI, budget calculation, or campaign estimates.",
        parameters=_schema_obj(
            {
                "cpc": genai_types.Schema(type=genai_types.Type.NUMBER, description="Cost per click in currency"),
                "daily_budget": genai_types.Schema(type=genai_types.Type.NUMBER, description="Daily budget in currency"),
                "conversion_rate": genai_types.Schema(type=genai_types.Type.NUMBER, description="Conversion rate as percentage (e.g. 2 for 2%)"),
                "avg_order_value": genai_types.Schema(type=genai_types.Type.NUMBER, description="Average order value in currency"),
            },
            ["cpc", "daily_budget", "conversion_rate", "avg_order_value"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="keyword_research_analyze",
        description="Get related keywords and difficulty for a seed keyword. Use when the user asks for keyword ideas, related keywords, or keyword research.",
        parameters=_schema_obj(
            {"keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Seed keyword")},
            ["keyword"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="competitor_analyze",
        description="Analyze a competitor domain: ranking keywords, indexed pages, top content. Use when the user asks about a competitor site or domain analysis.",
        parameters=_schema_obj(
            {"domain": genai_types.Schema(type=genai_types.Type.STRING, description="Competitor domain (e.g. example.com)")},
            ["domain"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="content_topic_research",
        description="Get related searches and people-also-ask questions for a topic. Use for content ideas or topic research.",
        parameters=_schema_obj(
            {"keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Topic or keyword")},
            ["keyword"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="content_seo_analysis",
        description="Analyze text for SEO: word count, keyword count, density, readability. Use when the user wants to check content for a keyword.",
        parameters=_schema_obj(
            {
                "keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Target keyword"),
                "text": genai_types.Schema(type=genai_types.Type.STRING, description="Content text to analyze"),
            },
            ["keyword", "text"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="content_ai_suggestions",
        description="Get AI-generated SEO suggestions for a topic: title, meta description, outline, long-tail keywords. Use when the user wants content or SEO suggestions for a topic.",
        parameters=_schema_obj(
            {"keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Topic or keyword")},
            ["keyword"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="local_seo_business",
        description="Look up a local business by name and location. Use when the user asks about a business listing or local SEO for a business.",
        parameters=_schema_obj(
            {
                "business_name": genai_types.Schema(type=genai_types.Type.STRING, description="Business name"),
                "location": genai_types.Schema(type=genai_types.Type.STRING, description="City or area"),
            },
            ["business_name", "location"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="advanced_site_audit",
        description="Quick site audit: page title and meta description for a URL. Use when the user asks to audit a website or check title/meta.",
        parameters=_schema_obj(
            {"url": genai_types.Schema(type=genai_types.Type.STRING, description="Page URL")},
            ["url"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="advanced_onpage",
        description="Count how many times a keyword appears on a page. Use for on-page keyword check.",
        parameters=_schema_obj(
            {
                "url": genai_types.Schema(type=genai_types.Type.STRING, description="Page URL"),
                "keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Keyword to count"),
            },
            ["url", "keyword"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="advanced_position",
        description="Find Google search position of a domain for a keyword. Use when the user asks where a site ranks for a keyword.",
        parameters=_schema_obj(
            {
                "domain": genai_types.Schema(type=genai_types.Type.STRING, description="Domain (e.g. example.com)"),
                "keyword": genai_types.Schema(type=genai_types.Type.STRING, description="Search keyword"),
            },
            ["domain", "keyword"],
        ),
    ),
    genai_types.FunctionDeclaration(
        name="advanced_backlinks",
        description="Estimate backlinks/mentions for a domain. Use when the user asks about backlinks or mentions.",
        parameters=_schema_obj(
            {"domain": genai_types.Schema(type=genai_types.Type.STRING, description="Domain to check")},
            ["domain"],
        ),
    ),
]

CHATBOT_TOOL = genai_types.Tool(function_declarations=CHATBOT_FUNCTION_DECLARATIONS)

# Map function name -> (method, path, body_keys for JSON)
_CHATBOT_API_MAP = {
    "ai_visibility_analyze": ("POST", "/api/ai-visibility/analyze", ["brand_name", "keyword"]),
    "ppc_ads": ("POST", "/api/ppc/ads", ["keyword"]),
    "ppc_calculator": ("POST", "/api/ppc/calculator", ["cpc", "daily_budget", "conversion_rate", "avg_order_value"]),
    "keyword_research_analyze": ("POST", "/api/keyword-research/analyze", ["keyword"]),
    "competitor_analyze": ("POST", "/api/competitor/analyze", ["domain"]),
    "content_topic_research": ("POST", "/api/content/topic-research", ["keyword"]),
    "content_seo_analysis": ("POST", "/api/content/seo-analysis", ["keyword", "text"]),
    "content_ai_suggestions": ("POST", "/api/content/ai-suggestions", ["keyword"]),
    "local_seo_business": ("POST", "/api/local-seo/business", ["business_name", "location"]),
    "advanced_site_audit": ("POST", "/api/advanced/site-audit", ["url"]),
    "advanced_onpage": ("POST", "/api/advanced/onpage", ["url", "keyword"]),
    "advanced_position": ("POST", "/api/advanced/position", ["domain", "keyword"]),
    "advanced_backlinks": ("POST", "/api/advanced/backlinks", ["domain"]),
}


def _execute_chatbot_function(name, args):
    """Execute a chatbot function by calling the corresponding API via test client. Returns dict with result or error."""
    if name not in _CHATBOT_API_MAP:
        return {"error": f"Unknown function: {name}"}
    method, path, body_keys = _CHATBOT_API_MAP[name]
    body = {k: args.get(k) for k in body_keys if k in args}
    with app.test_client() as c:
        if method == "POST":
            r = c.post(path, json=body)
        else:
            r = c.get(path)
    try:
        data = r.get_json()
    except Exception:
        data = {"raw": r.data.decode("utf-8") if r.data else ""}
    if r.status_code >= 400:
        return {"error": data.get("error", "Request failed"), "status_code": r.status_code, "response": data}
    return data


def normalize_url(url):
    if not url or not url.strip():
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def normalize_domain(domain):
    domain = (domain or "").lower()
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "")
    domain = domain.replace(".com", "").replace(".in", "").strip()
    return domain


def normalize_domain_comp(domain):
    if not domain:
        return ""
    if domain.startswith("http"):
        domain = urlparse(domain).netloc
    return domain.replace("www.", "")


# ============ 1. AI Visibility ============
@app.route("/api/ai-visibility/analyze", methods=["POST"])
def ai_visibility_analyze():
    data = request.get_json() or {}
    brand_name = (data.get("brand_name") or "").strip()
    keyword = (data.get("keyword") or "").strip()
    if not brand_name or not keyword:
        return jsonify({"error": "Please provide both brand_name and keyword"}), 400

    params = {"engine": "google", "q": keyword, "api_key": SERP_API_KEY}
    resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
    serp_data = resp.json()
    organic_results = serp_data.get("organic_results", [])
    brand_positions = []
    for result in organic_results:
        title = (result.get("title") or "").lower()
        snippet = (result.get("snippet") or "").lower()
        if brand_name.lower() in title or brand_name.lower() in snippet:
            brand_positions.append(result.get("position"))
    google_score = max(0, 100 - min(brand_positions) * 5) if brand_positions else 0

    ai_text = ""
    ai_score = 0
    if client_visibility:
        try:
            response = client_visibility.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"What are the best companies for {keyword}? Provide a detailed answer.",
            )
            ai_text = (response.text or "").lower()
            ai_score = 100 if brand_name.lower() in ai_text else 0
        except Exception as e:
            ai_text = str(e)
    else:
        ai_text = "GEMINI_API_KEY not set"

    final_score = round((google_score * 0.6) + (ai_score * 0.4), 2)
    return jsonify({
        "brand_positions": brand_positions,
        "google_score": google_score,
        "ai_response_preview": ai_text[:500] if ai_text else "",
        "ai_score": ai_score,
        "final_visibility_score": final_score,
    })


# ============ 2. PPC & Ads ============
@app.route("/api/ppc/ads", methods=["POST"])
def ppc_ads():
    data = request.get_json() or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"error": "keyword required"}), 400
    params = {"engine": "google", "q": keyword, "gl": "us", "hl": "en", "api_key": SERP_API_KEY}
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    data_resp = resp.json()
    ads = []
    for item in data_resp.get("immersive_products", []):
        ads.append({
            "ad_type": "Product Ad",
            "title": item.get("title"),
            "price": item.get("price"),
            "source": item.get("source"),
            "product_link": item.get("serpapi_link"),
        })
    return jsonify({"ads": ads})


@app.route("/api/ppc/calculator", methods=["POST"])
def ppc_calculator():
    data = request.get_json() or {}
    cpc = float(data.get("cpc", 1))
    daily_budget = float(data.get("daily_budget", 50))
    conversion_rate = float(data.get("conversion_rate", 2))
    avg_order_value = float(data.get("avg_order_value", 100))
    clicks = daily_budget / cpc if cpc > 0 else 0
    conversions = clicks * (conversion_rate / 100)
    revenue = conversions * avg_order_value
    profit = revenue - daily_budget
    return jsonify({
        "estimated_clicks_per_day": round(clicks, 2),
        "estimated_conversions_per_day": round(conversions, 2),
        "estimated_revenue_per_day": round(revenue, 2),
        "estimated_profit_loss": round(profit, 2),
    })


# ============ 3. Keyword Research ============
@app.route("/api/keyword-research/analyze", methods=["POST"])
def keyword_research_analyze():
    data = request.get_json() or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"error": "keyword required"}), 400
    try:
        url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
        r = requests.get(url, timeout=10)
        related_keywords = r.json()[1]
    except Exception:
        related_keywords = []

    results = []
    for kw in related_keywords:
        params = {"engine": "google", "q": kw, "api_key": SERP_API_KEY}
        r2 = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        info = r2.json().get("search_information", {})
        results_count = info.get("total_results", 0)
        if results_count > 50_000_000:
            difficulty = "High"
        elif results_count > 10_000_000:
            difficulty = "Medium"
        else:
            difficulty = "Low"
        results.append({
            "keyword": kw,
            "estimated_search_volume_proxy": results_count,
            "difficulty": difficulty,
        })
    return jsonify({"keywords": results})


# ============ 4. Competitor Analysis ============
SEED_KEYWORDS = [
    "learn python", "data structures", "python tutorial", "coding interview",
    "java tutorial", "web development", "javascript tutorial", "machine learning", "sql tutorial",
]


@app.route("/api/competitor/analyze", methods=["POST"])
def competitor_analyze():
    data = request.get_json() or {}
    domain_input = (data.get("domain") or "").strip()
    if not domain_input:
        return jsonify({"error": "domain required"}), 400
    domain = normalize_domain_comp(domain_input)

    keywords_data = []
    for keyword in SEED_KEYWORDS:
        params = {"engine": "google", "q": keyword, "api_key": SERP_API_KEY}
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        organic = resp.json().get("organic_results", [])
        for idx, result in enumerate(organic):
            link = result.get("link", "")
            if domain in link:
                keywords_data.append({"keyword": keyword, "position": idx + 1})
                break

    query = f"site:{domain}"
    params = {"engine": "google", "q": query, "api_key": SERP_API_KEY}
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    traffic_estimate = resp.json().get("search_information", {}).get("total_results", 0)

    top_pages = []
    for result in resp.json().get("organic_results", [])[:10]:
        top_pages.append({"title": result.get("title"), "url": result.get("link")})

    return jsonify({
        "ranking_keywords": keywords_data,
        "estimated_indexed_pages": traffic_estimate,
        "top_ranking_content": top_pages,
    })


# ============ 5. Content Marketing ============
@app.route("/api/content/topic-research", methods=["POST"])
def content_topic_research():
    data = request.get_json() or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"error": "keyword required"}), 400
    params = {"engine": "google", "q": keyword, "api_key": SERP_API_KEY}
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    d = resp.json()
    related_searches = [x["query"] for x in d.get("related_searches", [])]
    people_also_ask = []
    for item in d.get("related_questions", []):
        people_also_ask.append(item.get("question", item.get("query", "")))
    return jsonify({"related_searches": related_searches, "people_also_ask": people_also_ask})


@app.route("/api/content/seo-analysis", methods=["POST"])
def content_seo_analysis():
    data = request.get_json() or {}
    keyword = (data.get("keyword") or "").strip()
    text = (data.get("text") or "").strip()
    if not keyword:
        return jsonify({"error": "keyword required"}), 400
    word_count = len(text.split())
    keyword_count = text.lower().count(keyword.lower())
    density = (keyword_count / word_count) * 100 if word_count else 0
    readability = textstat.flesch_reading_ease(text) if text else 0
    return jsonify({
        "word_count": word_count,
        "keyword_count": keyword_count,
        "keyword_density_percent": round(density, 2),
        "readability_score": round(readability, 2),
    })


@app.route("/api/content/ai-suggestions", methods=["POST"])
def content_ai_suggestions():
    data = request.get_json() or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"error": "keyword required"}), 400
    if not client_new:
        return jsonify({"error": "AI client not configured"}), 503
    prompt = f'''You are an SEO expert. For the topic: "{keyword}" Generate:
1. SEO-optimized blog title
2. 160-character meta description
3. Blog outline with H2 and H3 headings
4. 10 related long-tail keywords'''
    try:
        response = client_new.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return jsonify({"suggestions": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ 6. Local SEO ============
@app.route("/api/local-seo/business", methods=["POST"])
def local_seo_business():
    data = request.get_json() or {}
    business_name = (data.get("business_name") or "").strip()
    location = (data.get("location") or "").strip()
    if not business_name or not location:
        return jsonify({"error": "business_name and location required"}), 400
    params = {"query": f"{business_name} in {location}", "key": GOOGLE_MAPS_API_KEY}
    resp = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params, timeout=10)
    results = resp.json().get("results", [])
    if not results:
        return jsonify({"found": False, "business": None})
    return jsonify({"found": True, "business": results[0]})


# ============ 7. Advanced SEO ============
@app.route("/api/advanced/site-audit", methods=["POST"])
def advanced_site_audit():
    data = request.get_json() or {}
    url = normalize_url((data.get("url") or "").strip())
    if not url:
        return jsonify({"error": "url required"}), 400
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        title = soup.title.string if soup.title else "Missing"
        meta = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta["content"] if meta and meta.get("content") else "Missing"
        return jsonify({"title": title, "meta_description": meta_desc})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/advanced/onpage", methods=["POST"])
def advanced_onpage():
    data = request.get_json() or {}
    url = normalize_url((data.get("url") or "").strip())
    keyword = (data.get("keyword") or "").strip()
    if not url or not keyword:
        return jsonify({"error": "url and keyword required"}), 400
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text().lower()
        keyword_count = text.count(keyword.lower())
        return jsonify({"keyword_count": keyword_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/advanced/position", methods=["POST"])
def advanced_position():
    data = request.get_json() or {}
    domain = (data.get("domain") or "").strip().replace("www.", "")
    keyword = (data.get("keyword") or "").strip()
    if not domain or not keyword:
        return jsonify({"error": "domain and keyword required"}), 400
    for start in range(0, 100, 10):
        params = {"engine": "google", "q": keyword, "start": start, "api_key": SERP_API_KEY}
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        organic = resp.json().get("organic_results", [])
        for idx, result in enumerate(organic):
            if domain in result.get("link", ""):
                return jsonify({"position": start + idx + 1, "found": True})
    return jsonify({"position": None, "found": False})


@app.route("/api/advanced/backlinks", methods=["POST"])
def advanced_backlinks():
    data = request.get_json() or {}
    domain = (data.get("domain") or "").strip()
    if not domain:
        return jsonify({"error": "domain required"}), 400
    query = f'"{domain}" -site:{domain}'
    params = {"engine": "google", "q": query, "api_key": SERP_API_KEY}
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    total = resp.json().get("search_information", {}).get("total_results", 0)
    return jsonify({"estimated_mentions": total})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# ============ Chatbot: Gemini with function calling ============

@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    """
    Smart SEO chatbot.
    - Uses API tools when required
    - Uses Gemini knowledge when no tool is needed
    - Calls tools automatically
    """

    if not client_chatbot:
        return jsonify({"error": "GEMINI_API_KEY not set"}), 503

    data = request.get_json() or {}
    message = (data.get("message") or data.get("query") or "").strip()

    if not message:
        return jsonify({"error": "message required"}), 400

    system_prompt = """
You are an expert SEO assistant for a Mini Semrush toolkit.

You have access to several tools that can fetch real SEO data.

IMPORTANT RULES:

1. If the user's question can be answered using a tool, CALL the tool.
2. If the user asks something general (SEO advice, marketing tips, explanations), answer normally using your own knowledge.
3. If a tool requires parameters and the user didn't provide them, ask the user for them.
4. After calling a tool and receiving results, summarize them clearly for the user.
5. Always respond in a helpful SEO expert tone.
"""

    conversation = [
        genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)]
        )
    ]

    config = genai_types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[CHATBOT_TOOL]
    )

    MAX_ITERATIONS = 6

    for _ in range(MAX_ITERATIONS):

        response = client_chatbot.models.generate_content(
            model="gemini-2.5-flash",
            contents=conversation,
            config=config
        )

        if not response.candidates:
            return jsonify({"reply": "Sorry, I couldn't process that."})

        candidate = response.candidates[0]

        if not candidate.content:
            return jsonify({"reply": "No response from AI."})

        parts = candidate.content.parts

        text_response = ""
        function_calls = []

        for p in parts:

            if getattr(p, "text", None):
                text_response += p.text

            if getattr(p, "function_call", None):
                function_calls.append(p.function_call)

        # If no tool call -> return normal AI response
        if not function_calls:
            return jsonify({"reply": text_response.strip()})

        # Add model tool request to conversation
        conversation.append(
            genai_types.Content(
                role="model",
                parts=parts
            )
        )

        # Execute tool calls
        for call in function_calls:

            function_name = call.name
            args = call.args or {}

            result = _execute_chatbot_function(function_name, args)

            conversation.append(
                genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part(
                            function_response=genai_types.FunctionResponse(
                                name=function_name,
                                response=result
                            )
                        )
                    ]
                )
            )

    return jsonify({
        "reply": "I couldn't complete the request but here's what I found."
    })


if __name__ == "__main__":
    # use_reloader=False avoids restarts when files in venv change (e.g. google.genai),
    # which can cause clients to see "Cannot reach the API" during restart.
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
