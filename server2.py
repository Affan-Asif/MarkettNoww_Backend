# """
# Competitor Comparison API
# Run: python server2.py
# Frontend: http://127.0.0.1:5002/app
# """

# import os
# import requests
# from urllib.parse import urlparse

# from flask import Flask, request, jsonify, send_file
# from flask_cors import CORS
# from dotenv import load_dotenv

# load_dotenv()

# _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# FRONTEND_HTML = os.path.join(_THIS_DIR, "server2_frontend", "index.html")

# app = Flask(__name__)
# CORS(app)

# SERP_API_KEY = os.getenv("SERP_API_KEY")

# # -----------------------------
# # Fetch related keywords dynamically
# # -----------------------------
# def get_related_keywords(query):

#     params = {
#         "engine": "google",
#         "q": query,
#         "api_key": SERP_API_KEY
#     }

#     resp = requests.get(
#         "https://serpapi.com/search.json",
#         params=params,
#         timeout=30
#     )

#     data = resp.json()

#     keywords = set()

#     # related searches
#     for r in data.get("related_searches", []):
#         keywords.add(r.get("query"))

#     # organic titles as keywords
#     for r in data.get("organic_results", [])[:5]:
#         title = r.get("title")
#         if title:
#             keywords.add(title)

#     return list(keywords)[:10]


# # -----------------------------
# # Utility
# # -----------------------------
# def normalize_domain(domain):
#     parsed = urlparse(domain if "://" in domain else f"http://{domain}")
#     return parsed.netloc.replace("www.", "")


# # -----------------------------
# # Get rankings for domain
# # -----------------------------
# def get_domain_rankings(domain, keywords):

#     keyword_positions = []

#     for keyword in keywords:

#         params = {
#             "engine": "google",
#             "q": keyword,
#             "api_key": SERP_API_KEY
#         }

#         resp = requests.get(
#             "https://serpapi.com/search.json",
#             params=params,
#             timeout=30
#         )

#         results = resp.json().get("organic_results", [])

#         position = None

#         for idx, r in enumerate(results):
#             link = r.get("link", "")
#             if domain in link:
#                 position = idx + 1
#                 break

#         keyword_positions.append({
#             "keyword": keyword,
#             "position": position
#         })

#     return keyword_positions


# # -----------------------------
# # Get indexed pages
# # -----------------------------
# def get_indexed_pages(domain):

#     query = f"site:{domain}"

#     params = {
#         "engine": "google",
#         "q": query,
#         "api_key": SERP_API_KEY
#     }

#     resp = requests.get(
#         "https://serpapi.com/search.json",
#         params=params,
#         timeout=30
#     )

#     data = resp.json()

#     indexed_pages = data.get(
#         "search_information", {}
#     ).get("total_results", 0)

#     top_pages = []

#     for r in data.get("organic_results", [])[:10]:
#         top_pages.append({
#             "title": r.get("title"),
#             "url": r.get("link")
#         })

#     return indexed_pages, top_pages

# @app.route("/api/competitor/compare", methods=["POST"])
# def competitor_compare():

#     data = request.get_json() or {}

#     domain1_input = data.get("domain1")
#     domain2_input = data.get("domain2")
#     query = data.get("query")

#     if not domain1_input or not domain2_input or not query:
#         return jsonify({"error": "domain1, domain2 and query required"}), 400

#     domain1 = normalize_domain(domain1_input)
#     domain2 = normalize_domain(domain2_input)

#     # dynamically fetch keywords
#     keywords = get_related_keywords(query)

#     rankings1 = get_domain_rankings(domain1, keywords)
#     rankings2 = get_domain_rankings(domain2, keywords)

#     pages1, top_pages1 = get_indexed_pages(domain1)
#     pages2, top_pages2 = get_indexed_pages(domain2)

#     keyword_compare = []

#     for k in keywords:

#         pos1 = next((x["position"] for x in rankings1 if x["keyword"] == k), None)
#         pos2 = next((x["position"] for x in rankings2 if x["keyword"] == k), None)

#         keyword_compare.append({
#             "keyword": k,
#             "company1_position": pos1,
#             "company2_position": pos2
#         })

#     graph_data = {
#         "labels": keywords,
#         "company1": [x["position"] for x in rankings1],
#         "company2": [x["position"] for x in rankings2]
#     }

#     return jsonify({
#         "keywords_used": keywords,
#         "keyword_comparison": keyword_compare,
#         "graph_data": graph_data,
#         "summary": {
#             "domain1": {"domain": domain1, "indexed_pages": pages1},
#             "domain2": {"domain": domain2, "indexed_pages": pages2}
#         }
#     })


# # -----------------------------
# # Health check & frontend
# # -----------------------------
# @app.route("/")
# def home():
#     return {"status": "Competitor Analysis API running"}


# @app.route("/app")
# def frontend():

#     """Serve the competitor comparison frontend."""
#     if not os.path.isfile(FRONTEND_HTML):
#         return jsonify({"error": "Frontend not found"}), 404
#     return send_file(FRONTEND_HTML)


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5002, debug=True, use_reloader=False)






# """
# Competitor Comparison API
# Run: python server2.py
# Frontend: http://127.0.0.1:5002/app
# """

# import os
# import requests
# from urllib.parse import urlparse

# from flask import Flask, request, jsonify, send_file
# from flask_cors import CORS
# from dotenv import load_dotenv

# load_dotenv()

# _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# FRONTEND_HTML = os.path.join(_THIS_DIR, "server2_frontend", "index.html")

# app = Flask(__name__)
# CORS(app)

# SERP_API_KEY = os.getenv("SERP_API_KEY")


# # ------------------------------------------------
# # Utility functions
# # ------------------------------------------------

# def normalize_domain(domain):
#     parsed = urlparse(domain if "://" in domain else f"http://{domain}")
#     return parsed.netloc.replace("www.", "")


# def extract_domain(url):
#     try:
#         parsed = urlparse(url)
#         return parsed.netloc.replace("www.", "")
#     except:
#         return ""


# # ------------------------------------------------
# # Get related keywords dynamically
# # ------------------------------------------------

# def get_related_keywords(query):

#     params = {
#         "engine": "google",
#         "q": query,
#         "api_key": SERP_API_KEY
#     }

#     resp = requests.get(
#         "https://serpapi.com/search.json",
#         params=params,
#         timeout=30
#     )

#     data = resp.json()

#     keywords = set()

#     # related searches
#     for r in data.get("related_searches", []):
#         q = r.get("query")
#         if q:
#             keywords.add(q)

#     # people also ask
#     for r in data.get("related_questions", []):
#         q = r.get("question")
#         if q:
#             keywords.add(q)

#     # titles
#     for r in data.get("organic_results", [])[:8]:
#         title = r.get("title")
#         if title:
#             keywords.add(title)

#     return list(keywords)[:12]


# # ------------------------------------------------
# # Get ranking positions
# # ------------------------------------------------

# def get_domain_rankings(domain, keywords):

#     keyword_positions = []

#     for keyword in keywords:

#         params = {
#             "engine": "google",
#             "q": keyword,
#             "num": 20,
#             "api_key": SERP_API_KEY
#         }

#         resp = requests.get(
#             "https://serpapi.com/search.json",
#             params=params,
#             timeout=30
#         )

#         results = resp.json().get("organic_results", [])

#         position = None

#         for idx, r in enumerate(results):

#             link = r.get("link", "")
#             result_domain = extract_domain(link)

#             if domain in result_domain:
#                 position = idx + 1
#                 break

#         keyword_positions.append({
#             "keyword": keyword,
#             "position": position
#         })

#     return keyword_positions


# # ------------------------------------------------
# # Indexed pages
# # ------------------------------------------------

# def get_indexed_pages(domain):

#     query = f"site:{domain}"

#     params = {
#         "engine": "google",
#         "q": query,
#         "api_key": SERP_API_KEY
#     }

#     resp = requests.get(
#         "https://serpapi.com/search.json",
#         params=params,
#         timeout=30
#     )

#     data = resp.json()

#     indexed_pages = data.get(
#         "search_information", {}
#     ).get("total_results", 0)

#     top_pages = []

#     for r in data.get("organic_results", [])[:10]:
#         top_pages.append({
#             "title": r.get("title"),
#             "url": r.get("link")
#         })

#     return indexed_pages, top_pages


# # ------------------------------------------------
# # Competitor comparison route
# # ------------------------------------------------

# @app.route("/api/competitor/compare", methods=["POST"])
# def competitor_compare():

#     data = request.get_json() or {}

#     domain1_input = data.get("domain1")
#     domain2_input = data.get("domain2")
#     query = data.get("query")

#     if not domain1_input or not domain2_input or not query:
#         return jsonify({"error": "domain1, domain2 and query required"}), 400

#     domain1 = normalize_domain(domain1_input)
#     domain2 = normalize_domain(domain2_input)

#     keywords = get_related_keywords(query)

#     rankings1 = get_domain_rankings(domain1, keywords)
#     rankings2 = get_domain_rankings(domain2, keywords)

#     pages1, top_pages1 = get_indexed_pages(domain1)
#     pages2, top_pages2 = get_indexed_pages(domain2)

#     keyword_compare = []

#     for k in keywords:

#         pos1 = next((x["position"] for x in rankings1 if x["keyword"] == k), None)
#         pos2 = next((x["position"] for x in rankings2 if x["keyword"] == k), None)

#         keyword_compare.append({
#             "keyword": k,
#             "company1_position": pos1,
#             "company2_position": pos2
#         })

#     graph_data = {
#         "labels": keywords,
#         "company1": [x["position"] for x in rankings1],
#         "company2": [x["position"] for x in rankings2]
#     }

#     return jsonify({
#         "keywords_used": keywords,
#         "keyword_comparison": keyword_compare,
#         "graph_data": graph_data,
#         "summary": {
#             "domain1": {
#                 "domain": domain1,
#                 "indexed_pages": pages1,
#                 "top_pages": top_pages1
#             },
#             "domain2": {
#                 "domain": domain2,
#                 "indexed_pages": pages2,
#                 "top_pages": top_pages2
#             }
#         }
#     })


# # ------------------------------------------------
# # Health check
# # ------------------------------------------------

# @app.route("/")
# def home():
#     return {"status": "Competitor Analysis API running"}


# @app.route("/app")
# def frontend():
#     if not os.path.isfile(FRONTEND_HTML):
#         return jsonify({"error": "Frontend not found"}), 404
#     return send_file(FRONTEND_HTML)


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5002, debug=True, use_reloader=False)



















"""
Competitor Comparison API
Run: python server2.py
Frontend: http://127.0.0.1:5002/app
"""

import os
import requests
from urllib.parse import urlparse

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

SERP_API_KEY = os.getenv("SERP_API_KEY")

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_HTML = os.path.join(_THIS_DIR, "server2_frontend", "index.html")


# -----------------------------
# Utilities
# -----------------------------

def normalize_domain(domain):
    parsed = urlparse(domain if "://" in domain else f"http://{domain}")
    return parsed.netloc.replace("www.", "")


def extract_domain(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except:
        return ""


def brand_name(domain):
    return domain.split(".")[0]


# -----------------------------
# Dynamic keyword generator
# -----------------------------

def get_related_keywords(query):

    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY
    }

    r = requests.get(
        "https://serpapi.com/search.json",
        params=params,
        timeout=30
    )

    data = r.json()

    keywords = set()

    for r in data.get("related_searches", []):
        if r.get("query"):
            keywords.add(r["query"])

    for r in data.get("related_questions", []):
        if r.get("question"):
            keywords.add(r["question"])

    for r in data.get("organic_results", [])[:6]:
        if r.get("title"):
            keywords.add(r["title"])

    return list(keywords)[:10]


# -----------------------------
# Ranking detection
# -----------------------------

def get_domain_rankings(domain, keywords):

    brand = brand_name(domain)

    keyword_positions = []

    for keyword in keywords:

        position = None

        for page in range(3):

            params = {
                "engine": "google",
                "q": keyword,
                "start": page * 10,
                "num": 10,
                "api_key": SERP_API_KEY
            }

            r = requests.get(
                "https://serpapi.com/search.json",
                params=params,
                timeout=30
            )

            results = r.json().get("organic_results", [])

            for idx, result in enumerate(results):

                link = result.get("link", "")
                title = result.get("title", "").lower()

                result_domain = extract_domain(link)

                if domain in result_domain or brand in title:
                    position = page * 10 + idx + 1
                    break

            if position:
                break

        keyword_positions.append({
            "keyword": keyword,
            "position": position
        })

    return keyword_positions


# -----------------------------
# Indexed pages
# -----------------------------

def get_indexed_pages(domain):

    params = {
        "engine": "google",
        "q": f"site:{domain}",
        "api_key": SERP_API_KEY
    }

    r = requests.get(
        "https://serpapi.com/search.json",
        params=params,
        timeout=30
    )

    data = r.json()

    indexed_pages = data.get(
        "search_information", {}
    ).get("total_results", 0)

    top_pages = []

    for result in data.get("organic_results", [])[:10]:
        top_pages.append({
            "title": result.get("title"),
            "url": result.get("link")
        })

    return indexed_pages, top_pages


# -----------------------------
# Competitor API
# -----------------------------

@app.route("/api/competitor/compare", methods=["POST"])
def competitor_compare():

    data = request.get_json() or {}

    domain1 = normalize_domain(data.get("domain1", ""))
    domain2 = normalize_domain(data.get("domain2", ""))
    query = data.get("query")

    if not domain1 or not domain2 or not query:
        return jsonify({"error": "domain1, domain2, query required"}), 400

    keywords = get_related_keywords(query)

    rankings1 = get_domain_rankings(domain1, keywords)
    rankings2 = get_domain_rankings(domain2, keywords)

    pages1, top_pages1 = get_indexed_pages(domain1)
    pages2, top_pages2 = get_indexed_pages(domain2)

    keyword_compare = []

    for k in keywords:

        pos1 = next((x["position"] for x in rankings1 if x["keyword"] == k), None)
        pos2 = next((x["position"] for x in rankings2 if x["keyword"] == k), None)

        keyword_compare.append({
            "keyword": k,
            "company1_position": pos1,
            "company2_position": pos2
        })

    # Graph data for frontend charts
    graph_data = {
        "labels": keywords,
        "company1": [x["position"] for x in rankings1],
        "company2": [x["position"] for x in rankings2]
    }

    return jsonify({

        "keywords_used": keywords,

        "keyword_comparison": keyword_compare,

        "graph_data": graph_data,

        "summary": {
            "domain1": {
                "domain": domain1,
                "indexed_pages": pages1,
                "top_pages": top_pages1
            },
            "domain2": {
                "domain": domain2,
                "indexed_pages": pages2,
                "top_pages": top_pages2
            }
        }
    })


# -----------------------------
# Health
# -----------------------------

@app.route("/")
def home():
    return {"status": "Competitor API running"}


@app.route("/app")
def frontend():
    if not os.path.isfile(FRONTEND_HTML):
        return jsonify({"error": "Frontend not found"}), 404
    return send_file(FRONTEND_HTML)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)