"""
Lightweight crawler for CLI — uses httpx (no JS rendering).
For JS-heavy sites the SaaS backend uses Playwright.
"""
import re
import json
from urllib.parse import urlparse
from dataclasses import dataclass, field

import httpx


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GEOBot/1.0; +https://causabi.com/bot)",
    "Accept": "text/html,application/xhtml+xml,*/*",
}


@dataclass
class CrawlResult:
    url: str
    domain: str
    title: str | None = None
    description: str | None = None
    business_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    social: dict = field(default_factory=dict)
    existing_schema: list = field(default_factory=list)
    body_text: str = ""
    pages: list = field(default_factory=list)
    ok: bool = True
    error: str | None = None


async def crawl_site(url: str) -> CrawlResult:
    """Fetch homepage and extract structured data."""
    if not url.startswith("http"):
        url = "https://" + url

    domain = urlparse(url).netloc.replace("www.", "")

    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=15.0, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        return CrawlResult(url=url, domain=domain, ok=False, error=str(e))

    title = _extract(html, r"<title[^>]*>([^<]+)</title>")
    desc = (
        _meta(html, "description")
        or _meta(html, "og:description")
    )
    og_title = _meta(html, "og:title")
    h1 = _extract(html, r"<h1[^>]*>([^<]+)</h1>")

    schemas = _extract_schemas(html)
    phone = _extract(html, r"(\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})")
    email = _extract(html, r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})")
    social = _extract_social(html)

    # Strip tags for body text
    body_text = re.sub(r"<[^>]+>", " ", html)
    body_text = re.sub(r"\s+", " ", body_text).strip()[:5000]

    page = {
        "url": url,
        "title": title,
        "description": desc,
        "schemas": schemas,
        "body_text": body_text,
        "phone": phone,
        "email": email,
        "social": social,
    }

    return CrawlResult(
        url=url,
        domain=domain,
        title=title,
        description=desc,
        business_name=og_title or h1 or title,
        phone=phone,
        email=email,
        social=social,
        existing_schema=schemas,
        body_text=body_text,
        pages=[page],
    )


def _extract(html: str, pattern: str) -> str | None:
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip() or None
    return None


def _meta(html: str, name: str) -> str | None:
    m = re.search(
        rf'<meta[^>]+(?:name|property)=["\'](?:og:)?{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE,
    ) or re.search(
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\'](?:og:)?{re.escape(name)}["\']',
        html, re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def _extract_schemas(html: str) -> list:
    schemas = []
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    ):
        try:
            data = json.loads(m.group(1).strip())
            if isinstance(data, list):
                schemas.extend(data)
            else:
                schemas.append(data)
        except Exception:
            pass
    return schemas


def _extract_social(html: str) -> dict:
    social = {}
    platforms = {
        "instagram": r'href=["\']([^"\']*instagram\.com/[^"\']+)["\']',
        "vk": r'href=["\']([^"\']*vk\.com/[^"\']+)["\']',
        "telegram": r'href=["\']([^"\']*(?:t\.me|telegram)[^"\']+)["\']',
        "youtube": r'href=["\']([^"\']*youtube\.com/[^"\']+)["\']',
        "twitter": r'href=["\']([^"\']*(?:twitter|x)\.com/[^"\']+)["\']',
        "linkedin": r'href=["\']([^"\']*linkedin\.com/[^"\']+)["\']',
    }
    for name, pattern in platforms.items():
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            social[name] = m.group(1)
    return social
