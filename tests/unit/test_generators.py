"""Tests for generators: schema, llms_txt, robots patcher."""
import json
import pytest
from geo_optimizer.core.crawler import CrawlResult
from geo_optimizer.generators.schema import generate_organization_schema
from geo_optimizer.generators.llms_txt import generate_llms_txt
from geo_optimizer.generators.robots import _patch


def _make_crawl(**kwargs) -> CrawlResult:
    defaults = dict(
        url="https://example.com",
        domain="example.com",
        title="Example Co",
        description="We do amazing things",
        business_name="Example Co",
        phone="+71234567890",
        email="info@example.com",
        address="123 Main St",
        social={"vk": "https://vk.com/example", "telegram": "https://t.me/example"},
        existing_schema=[],
        body_text="Some text",
        pages=[],
    )
    defaults.update(kwargs)
    return CrawlResult(**defaults)


class TestSchemaGenerator:
    def test_basic_structure(self):
        crawl = _make_crawl()
        result = json.loads(generate_organization_schema(crawl))
        assert result["@context"] == "https://schema.org"
        assert result["@type"] == "Organization"
        assert result["name"] == "Example Co"
        assert result["url"] == "https://example.com"

    def test_includes_description(self):
        crawl = _make_crawl()
        result = json.loads(generate_organization_schema(crawl))
        assert result["description"] == "We do amazing things"

    def test_includes_contact(self):
        crawl = _make_crawl()
        result = json.loads(generate_organization_schema(crawl))
        assert result["telephone"] == "+71234567890"
        assert result["email"] == "info@example.com"

    def test_includes_same_as(self):
        crawl = _make_crawl()
        result = json.loads(generate_organization_schema(crawl))
        assert "sameAs" in result
        assert len(result["sameAs"]) == 2

    def test_no_phone_omitted(self):
        crawl = _make_crawl(phone=None)
        result = json.loads(generate_organization_schema(crawl))
        assert "telephone" not in result

    def test_valid_json_output(self):
        crawl = _make_crawl()
        result = generate_organization_schema(crawl)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)


class TestLlmsTxtGenerator:
    def test_starts_with_name(self):
        crawl = _make_crawl()
        result = generate_llms_txt(crawl)
        assert result.startswith("# Example Co")

    def test_includes_description(self):
        crawl = _make_crawl()
        result = generate_llms_txt(crawl)
        assert "We do amazing things" in result

    def test_includes_contact_section(self):
        crawl = _make_crawl()
        result = generate_llms_txt(crawl)
        assert "## Contact" in result
        assert "+71234567890" in result
        assert "info@example.com" in result

    def test_includes_links_section(self):
        crawl = _make_crawl()
        result = generate_llms_txt(crawl)
        assert "## Links" in result
        assert "vk.com/example" in result

    def test_no_phone_no_contact_section(self):
        crawl = _make_crawl(phone=None, email=None, address=None)
        result = generate_llms_txt(crawl)
        assert "## Contact" not in result

    def test_markdown_format(self):
        """llms.txt must be valid markdown with h1 header."""
        crawl = _make_crawl()
        result = generate_llms_txt(crawl)
        lines = result.splitlines()
        assert lines[0].startswith("# ")


class TestRobotsPatcher:
    def test_adds_missing_bots(self):
        result = _patch("", "https://example.com")
        assert "GPTBot" in result
        assert "ClaudeBot" in result
        assert "PerplexityBot" in result

    def test_does_not_duplicate_existing_bot(self):
        existing = "User-agent: GPTBot\nAllow: /"
        result = _patch(existing, "https://example.com")
        assert result.count("GPTBot") == 1

    def test_adds_llms_txt_reference(self):
        result = _patch("", "https://example.com")
        assert "llms.txt" in result

    def test_preserves_existing_content(self):
        existing = "User-agent: *\nDisallow: /admin"
        result = _patch(existing, "https://example.com")
        assert "User-agent: *" in result
        assert "Disallow: /admin" in result

    def test_no_changes_if_all_present(self):
        bots = [
            "GPTBot", "ClaudeBot", "anthropic-ai", "PerplexityBot",
            "CCBot", "Google-Extended", "Bytespider", "YouBot",
            "cohere-ai", "ia_archiver",
        ]
        existing = "\n".join(
            f"User-agent: {b}\nAllow: /" for b in bots
        ) + "\n# llms.txt: https://example.com/llms.txt"
        result = _patch(existing, "https://example.com")
        assert result == existing


class TestScorerDigitalTypes:
    """Verify SoftwareApplication/WebSite schema types score correctly."""
    from geo_optimizer.core.robots import RobotsAudit
    from geo_optimizer.core.scorer import calculate_score

    def _robots(self):
        from geo_optimizer.core.robots import RobotsAudit
        return RobotsAudit(has_robots_txt=False, blocked_bots=[], allowed_bots=[], ai_blocking_score=0)

    def test_software_application_scores_high(self):
        from geo_optimizer.core.scorer import calculate_score
        crawl = {
            "existing_schema": [{
                "@context": "https://schema.org",
                "@type": "SoftwareApplication",
                "name": "My App",
                "description": "Great software",
                "url": "https://example.com",
                "offers": {"@type": "Offer", "price": "0"},
            }],
            "body_text": "word " * 600,
            "pages": [],
            "business_name": "My App",
            "phone": None, "email": None, "address": None, "social": {},
        }
        result = calculate_score(crawl, self._robots())
        assert result.breakdown.schema_org >= 15

    def test_website_schema_scores_correctly(self):
        from geo_optimizer.core.scorer import calculate_score
        crawl = {
            "existing_schema": [{"@type": "WebSite", "name": "Test"}],
            "body_text": "word " * 600,
            "pages": [],
            "business_name": "Test", "phone": None, "email": None, "address": None, "social": {},
        }
        result = calculate_score(crawl, self._robots())
        assert result.breakdown.schema_org >= 15
