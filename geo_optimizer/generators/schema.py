"""
Schema.org JSON-LD generator for CLI.
"""
import json
from geo_optimizer.core.crawler import CrawlResult


def generate_organization_schema(crawl: CrawlResult) -> str:
    """Generate Organization JSON-LD from crawl data."""
    schema: dict = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": crawl.business_name or crawl.domain,
        "url": crawl.url,
    }

    if crawl.description:
        schema["description"] = crawl.description
    if crawl.phone:
        schema["telephone"] = crawl.phone
    if crawl.email:
        schema["email"] = crawl.email
    if crawl.address:
        schema["address"] = {
            "@type": "PostalAddress",
            "streetAddress": crawl.address,
        }

    same_as = list(crawl.social.values()) if crawl.social else []
    if same_as:
        schema["sameAs"] = same_as

    return json.dumps(schema, ensure_ascii=False, indent=2)
