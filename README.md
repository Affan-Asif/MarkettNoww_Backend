# MarketNow / Mini Semrush – Flask API

REST API backend for the Mini Semrush toolkit. Used by the Next.js frontend after login.

## Setup

1. Create a virtualenv and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set:
   - `GEMINI_API_KEY` – for AI Visibility and Content AI suggestions
   - `SERPAPI_KEY` – for SerpAPI (search results, ads, keywords, etc.)
   - `GOOGLE_MAPS_API_KEY` – for Local SEO business lookup

## Run

```bash
python server.py
```

Server runs at **http://localhost:5001**. The Next.js app (after login) calls `NEXT_PUBLIC_API_URL` (default `http://localhost:5001`).

## Endpoints

- `POST /api/ai-visibility/analyze` – brand + keyword → visibility scores
- `POST /api/ppc/ads` – keyword → paid ads
- `POST /api/ppc/calculator` – CPC, budget, conversion → estimates
- `POST /api/keyword-research/analyze` – keyword → related keywords + difficulty
- `POST /api/competitor/analyze` – domain → ranking keywords, indexed pages, top content
- `POST /api/content/topic-research` – keyword → related searches, people also ask
- `POST /api/content/seo-analysis` – keyword + text → word count, density, readability
- `POST /api/content/ai-suggestions` – keyword → AI content suggestions
- `POST /api/local-seo/business` – business name + location → listing
- `POST /api/advanced/site-audit` – url → title, meta description
- `POST /api/advanced/onpage` – url + keyword → keyword count
- `POST /api/advanced/position` – domain + keyword → ranking position
- `POST /api/advanced/backlinks` – domain → estimated mentions
- `GET /api/health` – health check
