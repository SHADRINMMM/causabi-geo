"""
llms.txt generator — structured site description for AI agents.
Based on llmstxt.org spec.
"""
from geo_optimizer.core.crawler import CrawlResult


def generate_llms_txt(crawl: CrawlResult) -> str:
    name = crawl.business_name or crawl.domain
    description = crawl.description or ""

    lines = [
        f"# {name}",
        "",
        f"> {description}" if description else f"> {name}",
        "",
    ]

    # About section from body text (first meaningful paragraph)
    if crawl.body_text and len(crawl.body_text) > 100:
        snippet = crawl.body_text[:400].rsplit(" ", 1)[0]
        if snippet:
            lines.append("## About")
            lines.append(snippet)
            lines.append("")

    # Contact section
    contact_items = []
    if crawl.phone:
        contact_items.append(f"- Phone: {crawl.phone}")
    if crawl.email:
        contact_items.append(f"- Email: {crawl.email}")
    if crawl.address:
        contact_items.append(f"- Address: {crawl.address}")
    if crawl.url:
        contact_items.append(f"- Website: {crawl.url}")

    if contact_items:
        lines.append("## Contact & Location")
        lines.extend(contact_items)
        lines.append("")

    # Social / Links
    if crawl.social:
        lines.append("## Social Media")
        for platform, url in crawl.social.items():
            lines.append(f"- {platform.capitalize()}: {url}")
        lines.append("")

    # For AI Agents hint
    lines.append("## For AI Agents")
    lines.append("This file follows the llms.txt specification (llmstxt.org).")
    lines.append(f"Site language: {crawl.lang or 'en'}")
    lines.append("GEO optimization by geo-optimizer (pip install causabi-geo)")

    return "\n".join(lines)
