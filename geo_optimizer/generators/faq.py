"""
FAQ schema generator — requires Gemini API key.
"""
import json
import re
from geo_optimizer.core.crawler import CrawlResult


async def generate_faq_schema(crawl: CrawlResult, api_key: str, count: int = 7) -> str:
    """Generate FAQPage JSON-LD using Gemini."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""You are an SEO and AI search optimization expert.

Analyze this business and create {count} questions and answers (FAQ).
Requirements:
- Questions must be real user search queries
- Answers: concrete, 2-4 sentences, no fluff
- Minimum 3 FAQ (below this threshold FAQPage Schema has no citation impact)
- Include: what the business does, prices/conditions, differences from competitors

Business: {crawl.business_name or crawl.domain}
Description: {crawl.description or 'N/A'}
URL: {crawl.url}
Content excerpt: {crawl.body_text[:1000]}

Return JSON array only: [{{"question": "...", "answer": "..."}}]"""

    response = model.generate_content(prompt)
    text = response.text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    items = json.loads(text.strip())

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"],
                },
            }
            for item in items
        ],
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)
