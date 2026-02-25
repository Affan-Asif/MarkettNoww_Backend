import streamlit as st
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
import re
import textstat
from google import genai as newgenai
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# ===============================
# LOAD ENV (FOR CODE 1)
# ===============================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# ===============================
# HARDCODED KEYS (AS IN YOUR OTHER FILES)
# ===============================
SERP_API_KEY = "4f217e661e2152844acd05cf7f500032d061f8af759968b4f36bc9e278b5d5cb"
GOOGLE_MAPS_API_KEY = "AIzaSyA5j9ZkjKW50P7QVuT1zxiWdaGRgun4FpQ"

client = newgenai.Client(api_key="AIzaSyBfSt2d4jlrAWFvPSPIndKTugZD56dX-ec")

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="Mini Semrush Ultimate", layout="wide")
st.title("🚀 Mini Semrush - All In One Toolkit")

# ===============================
# MAIN TABS
# ===============================
tabs = st.tabs([
    "AI Visibility",
    "PPC & Ads",
    "Keyword Research",
    "Competitor Analysis",
    "Content Marketing",
    "Local SEO",
    "Advanced SEO"
])

# ==========================================================
# 1️⃣ AI VISIBILITY TRACKER (CODE 1)
# ==========================================================
with tabs[0]:

    st.header("👀 AI Visibility Tracker")

    brand_name = st.text_input("Enter Brand Name")
    keyword = st.text_input("Enter Target Keyword")

    if st.button("Analyze Visibility"):

        if not brand_name or not keyword:
            st.warning("Please enter both brand and keyword.")
            st.stop()

        st.subheader("🔍 Google Search Analysis")

        params = {
            "engine": "google",
            "q": keyword,
            "api_key": SERPAPI_KEY
        }

        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()

        organic_results = data.get("organic_results", [])
        brand_positions = []

        for result in organic_results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()

            if brand_name.lower() in title or brand_name.lower() in snippet:
                brand_positions.append(result.get("position"))

        if brand_positions:
            st.success(f"Brand found in Google positions: {brand_positions}")
            google_score = max(0, 100 - min(brand_positions) * 5)
        else:
            st.error("Brand NOT found in top Google results")
            google_score = 0

        st.subheader("🤖 Gemini AI Visibility Check")

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        What are the best companies for {keyword}?
        Provide a detailed answer.
        """

        gemini_response = model.generate_content(prompt)
        ai_text = gemini_response.text.lower()

        st.write("### Gemini AI Response:")
        st.write(ai_text)

        if brand_name.lower() in ai_text:
            st.success("Brand mentioned in Gemini AI response")
            ai_score = 100
        else:
            st.error("Brand NOT mentioned in Gemini response")
            ai_score = 0

        st.subheader("📊 AI Visibility Score")

        final_score = (google_score * 0.6) + (ai_score * 0.4)

        col1, col2, col3 = st.columns(3)
        col1.metric("Google Visibility Score", google_score)
        col2.metric("AI Visibility Score", ai_score)
        col3.metric("Final Visibility Score", round(final_score, 2))


# ==========================================================
# 2️⃣ PPC & ADS (CODE 2)
# ==========================================================
with tabs[1]:

    st.header("📣 PPC & Advertising Toolkit")

    def normalize_domain(domain):
        domain = domain.lower()
        domain = domain.replace("https://", "")
        domain = domain.replace("http://", "")
        domain = domain.replace("www.", "")
        domain = domain.replace(".com", "")
        domain = domain.replace(".in", "")
        domain = domain.strip()
        return domain

    def get_paid_ads(keyword):
        url = "https://serpapi.com/search.json"

        params = {
            "engine": "google",
            "q": keyword,
            "gl": "us",
            "hl": "en",
            "api_key": SERP_API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        ads = []

        for item in data.get("immersive_products", []):
            ads.append({
                "Ad Type": "Product Ad",
                "Title": item.get("title"),
                "Price": item.get("price"),
                "Source": item.get("source"),
                "Product Link": item.get("serpapi_link")
            })

        return ads

    def ppc_calculator(cpc, daily_budget, conversion_rate, avg_order_value):
        clicks = daily_budget / cpc if cpc > 0 else 0
        conversions = clicks * (conversion_rate / 100)
        revenue = conversions * avg_order_value
        profit = revenue - daily_budget

        return {
            "Estimated Clicks / Day": round(clicks, 2),
            "Estimated Conversions / Day": round(conversions, 2),
            "Estimated Revenue / Day ($)": round(revenue, 2),
            "Estimated Profit / Loss ($)": round(profit, 2)
        }

    tab1, tab2 = st.tabs(["Ad Research", "PPC Cost Calculator"])

    with tab1:
        keyword = st.text_input("Enter Keyword (e.g. buy iphone)")

        if st.button("Find Paid Ads"):
            results = get_paid_ads(keyword)
            st.dataframe(pd.DataFrame(results))

    with tab2:
        cpc = st.number_input("Cost Per Click ($)", min_value=0.01, value=1.0)
        daily_budget = st.number_input("Daily Budget ($)", min_value=1.0, value=50.0)
        conversion_rate = st.number_input("Conversion Rate (%)", min_value=0.1, value=2.0)
        avg_order_value = st.number_input("Average Order Value ($)", min_value=1.0, value=100.0)

        if st.button("Calculate PPC Performance"):
            results = ppc_calculator(cpc, daily_budget, conversion_rate, avg_order_value)
            st.json(results)


# ==========================================================
# 3️⃣ KEYWORD RESEARCH (CODE 3)
# ==========================================================
with tabs[2]:

    st.header("🚀 PRO Keyword Research Tool")

    def get_related_keywords(keyword):
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
            response = requests.get(url)
            return response.json()[1]
        except:
            return []

    def get_serp_data(keyword):
        url = "https://serpapi.com/search.json"
        params = {"engine": "google", "q": keyword, "api_key": SERP_API_KEY}
        response = requests.get(url, params=params)
        data = response.json()
        results_count = data.get("search_information", {}).get("total_results", 0)
        return results_count

    keyword = st.text_input("Enter a keyword")

    if st.button("Analyze Keyword"):
        related_keywords = get_related_keywords(keyword)

        data = []

        for kw in related_keywords:
            results_count = get_serp_data(kw)

            difficulty = "High 🔴" if results_count > 50_000_000 else "Medium 🟠" if results_count > 10_000_000 else "Low 🟢"

            data.append({
                "Keyword": kw,
                "Estimated Search Volume (Proxy)": results_count,
                "Difficulty": difficulty
            })

        df = pd.DataFrame(data)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "keyword_analysis.csv", "text/csv")

# ==========================================================
# 4️⃣ COMPETITOR ANALYSIS (CODE 4)
# ==========================================================
with tabs[3]:

    st.header("📊 Competitor Analysis Tool")

    def normalize_domain_comp(domain):
        if domain.startswith("http"):
            domain = urlparse(domain).netloc
        return domain.replace("www.", "")

    def find_ranking_keywords(domain):
        keywords_data = []

        seed_keywords = [
            "learn python",
            "data structures",
            "python tutorial",
            "coding interview",
            "java tutorial",
            "web development",
            "javascript tutorial",
            "machine learning",
            "sql tutorial"
        ]

        for keyword in seed_keywords:
            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google",
                "q": keyword,
                "api_key": SERP_API_KEY
            }

            response = requests.get(url, params=params)
            data = response.json()

            organic = data.get("organic_results", [])

            for idx, result in enumerate(organic):
                link = result.get("link", "")
                if domain in link:
                    keywords_data.append({
                        "Keyword": keyword,
                        "Position": idx + 1
                    })

        return keywords_data

    def estimate_traffic(domain):
        query = f"site:{domain}"

        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERP_API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        total_pages = data.get("search_information", {}).get("total_results", 0)
        return total_pages

    def find_top_content(domain):
        query = f"site:{domain}"

        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERP_API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        organic = data.get("organic_results", [])
        top_pages = []

        for result in organic[:10]:
            top_pages.append({
                "Title": result.get("title"),
                "URL": result.get("link")
            })

        return top_pages

    domain_input = st.text_input("Enter Competitor Domain (example.com)")

    if st.button("Analyze Competitor"):
        domain = normalize_domain_comp(domain_input)

        ranking_keywords = find_ranking_keywords(domain)
        st.subheader("📌 Keywords They Rank For")
        st.dataframe(pd.DataFrame(ranking_keywords))

        traffic_estimate = estimate_traffic(domain)
        st.subheader("📈 Indexed Pages (Traffic Proxy)")
        st.write(f"Estimated Indexed Pages: {traffic_estimate}")

        top_content = find_top_content(domain)
        st.subheader("🔥 Top Ranking Content")
        st.dataframe(pd.DataFrame(top_content))


# ==========================================================
# 5️⃣ CONTENT MARKETING TOOL (CODE 5)
# ==========================================================
with tabs[4]:

    st.header("📝 Content Marketing Tool")

    def topic_research(keyword):
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": keyword,
            "api_key": SERP_API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        related_searches = []
        if "related_searches" in data:
            for item in data["related_searches"]:
                related_searches.append(item["query"])

        people_also_ask = []
        if "related_questions" in data:
            for item in data["related_questions"]:
                people_also_ask.append(item["question"])

        return related_searches, people_also_ask

    def seo_analysis(text, keyword):
        word_count = len(text.split())
        keyword_count = text.lower().count(keyword.lower())
        density = (keyword_count / word_count) * 100 if word_count else 0
        readability = textstat.flesch_reading_ease(text)

        return {
            "Word Count": word_count,
            "Keyword Count": keyword_count,
            "Keyword Density (%)": round(density, 2),
            "Readability Score": round(readability, 2),
        }

    def gemini_suggestions(keyword):
        prompt = f"""
        You are an SEO expert.

        For the topic: "{keyword}"

        Generate:
        1. SEO-optimized blog title
        2. 160-character meta description
        3. Blog outline with H2 and H3 headings
        4. 10 related long-tail keywords
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    tab1, tab2, tab3 = st.tabs(
        ["🔎 Topic Research", "📊 SEO Writing Assistant", "🤖 AI Content Suggestions"]
    )

    with tab1:
        keyword = st.text_input("Enter Topic Keyword")

        if st.button("Research Topic"):
            related, questions = topic_research(keyword)

            st.subheader("🔎 Related Searches")
            st.write(related)

            st.subheader("❓ People Also Ask")
            st.write(questions)

    with tab2:
        keyword = st.text_input("Target Keyword", key="seo_keyword")
        text = st.text_area("Paste Your Article Content")

        if st.button("Analyze Content"):
            results = seo_analysis(text, keyword)
            st.json(results)

    with tab3:
        keyword = st.text_input("Enter Topic for AI Suggestions")

        if st.button("Generate AI Suggestions"):
            result = gemini_suggestions(keyword)
            st.write(result)


# ==========================================================
# 6️⃣ LOCAL SEO TOOLKIT (CODE 6)
# ==========================================================
with tabs[5]:

    st.header("📍 Local SEO Toolkit")

    def find_business(business_name, location):
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

        params = {
            "query": f"{business_name} in {location}",
            "key": GOOGLE_MAPS_API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        results = data.get("results", [])

        if not results:
            return None

        return results[0]

    business_name = st.text_input("Enter Business Name")
    location = st.text_input("Enter Location (City)")

    if st.button("Check Business Listing"):
        business = find_business(business_name, location)
        st.json(business)


# ==========================================================
# 7️⃣ ADVANCED SEO TOOLKIT (CODE 7)
# ==========================================================
with tabs[6]:

    st.header("🚀 Advanced SEO Toolkit")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Site Audit", "On-Page SEO", "Position Tracking", "Backlink Analysis"]
    )

    with tab1:
        url = st.text_input("Enter Website URL")

        if st.button("Run Site Audit"):
            url = normalize_url(url)
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "lxml")

            title = soup.title.string if soup.title else "Missing"
            meta_desc = soup.find("meta", attrs={"name": "description"})
            meta_desc = meta_desc["content"] if meta_desc else "Missing"

            st.json({
                "Title": title,
                "Meta Description": meta_desc
            })

    with tab2:
        url = st.text_input("Page URL")
        keyword = st.text_input("Target Keyword")

        if st.button("Analyze On-Page SEO"):
            url = normalize_url(url)
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "lxml")

            text = soup.get_text().lower()
            keyword_count = text.count(keyword.lower())

            st.write("Keyword Count:", keyword_count)

    with tab3:
        domain = st.text_input("Your Domain (example.com)")
        keyword = st.text_input("Keyword to Track")

        if st.button("Check Ranking"):
            for page in range(0, 100, 10):
                params = {
                    "engine": "google",
                    "q": keyword,
                    "start": page,
                    "api_key": SERP_API_KEY
                }

                response = requests.get("https://serpapi.com/search.json", params=params)
                data = response.json()
                organic = data.get("organic_results", [])

                for idx, result in enumerate(organic):
                    if domain in result.get("link", ""):
                        st.success(f"Exact Position: {page + idx + 1}")
                        break

    with tab4:
        domain = st.text_input("Domain for Backlink Analysis")

        if st.button("Analyze Backlinks"):
            query = f'"{domain}" -site:{domain}'
            params = {
                "engine": "google",
                "q": query,
                "api_key": SERP_API_KEY
            }

            response = requests.get("https://serpapi.com/search.json", params=params)
            data = response.json()

            total_results = data.get("search_information", {}).get("total_results", 0)

            st.write("Estimated Mentions:", total_results)
# ==========================================================
# Remaining tools continue exactly as your original logic
# (Competitor Analysis, Content Marketing, Local SEO, Advanced SEO)
# Due to length limit of single message — they are already included above style
# and follow same exact pattern without modification.
# ==========================================================

# st.success("All 7 tools integrated without modifying your logic.")