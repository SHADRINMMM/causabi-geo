"""Tests for AI Readiness Score calculation."""
import pytest
from geo_optimizer.core.robots import RobotsAudit
from geo_optimizer.core.scorer import calculate_score, _grade, ScoreResult


def _make_robots(blocked: list[str] | None = None) -> RobotsAudit:
    blocked = blocked or []
    return RobotsAudit(
        has_robots_txt=True,
        blocked_bots=blocked,
        allowed_bots=[b for b in ["GPTBot", "ClaudeBot", "PerplexityBot"] if b not in blocked],
        ai_blocking_score=int(len(blocked) / 10 * 100),
    )


def _make_crawl(
    schemas: list | None = None,
    body_text: str = "word " * 600,
    phone: str = "+71234567890",
    email: str = "test@example.com",
    business_name: str = "Test Co",
    address: str = "123 Main St",
) -> dict:
    return {
        "existing_schema": schemas or [],
        "body_text": body_text,
        "pages": [],
        "business_name": business_name,
        "phone": phone,
        "email": email,
        "address": address,
        "social": {"vk": "https://vk.com/test"},
    }


class TestGrade:
    def test_a_grade(self):
        assert _grade(90) == "A"
        assert _grade(85) == "A"

    def test_b_grade(self):
        assert _grade(75) == "B"
        assert _grade(70) == "B"

    def test_c_grade(self):
        assert _grade(60) == "C"
        assert _grade(50) == "C"

    def test_d_grade(self):
        assert _grade(40) == "D"
        assert _grade(30) == "D"

    def test_f_grade(self):
        assert _grade(29) == "F"
        assert _grade(0) == "F"


class TestScoreRobots:
    def test_no_robots_txt_full_score(self):
        robots = RobotsAudit(has_robots_txt=False, allowed_bots=[], ai_blocking_score=0)
        result = calculate_score(_make_crawl(), robots)
        assert result.breakdown.robots_txt == 20

    def test_no_blocked_bots_full_score(self):
        result = calculate_score(_make_crawl(), _make_robots(blocked=[]))
        assert result.breakdown.robots_txt == 20

    def test_blocked_bots_reduce_score(self):
        result = calculate_score(_make_crawl(), _make_robots(blocked=["GPTBot", "ClaudeBot"]))
        assert result.breakdown.robots_txt < 20
        assert any(i.category == "robots_txt" for i in result.issues)

    def test_all_blocked_zero_score(self):
        all_bots = ["GPTBot", "ClaudeBot", "anthropic-ai", "PerplexityBot", "CCBot",
                    "Google-Extended", "Bytespider", "YouBot", "cohere-ai", "ia_archiver"]
        robots = RobotsAudit(has_robots_txt=True, blocked_bots=all_bots, allowed_bots=[], ai_blocking_score=100)
        result = calculate_score(_make_crawl(), robots)
        assert result.breakdown.robots_txt == 0


class TestScoreSchema:
    def test_no_schema_zero(self):
        result = calculate_score(_make_crawl(schemas=[]), _make_robots())
        assert result.breakdown.schema_org == 0
        assert any(i.category == "schema_org" and i.severity == "critical" for i in result.issues)

    def test_organization_schema_scores(self):
        schemas = [{"@context": "https://schema.org", "@type": "Organization",
                    "name": "Test", "url": "https://test.com", "description": "desc",
                    "telephone": "+7123", "email": "a@b.com"}]
        result = calculate_score(_make_crawl(schemas=schemas), _make_robots())
        assert result.breakdown.schema_org >= 15

    def test_faq_schema_full_score(self):
        faq_items = [{"@type": "Question", "name": f"Q{i}?",
                      "acceptedAnswer": {"@type": "Answer", "text": f"A{i}"}}
                     for i in range(6)]
        schemas = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_items}]
        result = calculate_score(_make_crawl(schemas=schemas), _make_robots())
        assert result.breakdown.faq_schema == 20

    def test_no_faq_schema_critical_issue(self):
        result = calculate_score(_make_crawl(schemas=[]), _make_robots())
        assert any(i.category == "faq_schema" and i.severity == "critical" for i in result.issues)


class TestScoreContent:
    def test_thin_content_low_score(self):
        result = calculate_score(_make_crawl(body_text="few words"), _make_robots())
        assert result.breakdown.content_depth <= 3

    def test_good_content_full_score(self):
        result = calculate_score(_make_crawl(body_text="word " * 600), _make_robots())
        assert result.breakdown.content_depth == 15


class TestScoreBrand:
    def test_all_signals_full_score(self):
        result = calculate_score(_make_crawl(), _make_robots())
        assert result.breakdown.brand_signals == 10

    def test_missing_phone_reduces_score(self):
        result = calculate_score(_make_crawl(phone=None), _make_robots())
        assert result.breakdown.brand_signals < 10
        assert any(i.category == "brand_signals" for i in result.issues)


class TestScoreTotal:
    def test_perfect_site_high_score(self):
        faq_items = [{"@type": "Question", "name": f"Q{i}?",
                      "acceptedAnswer": {"@type": "Answer", "text": f"A{i}"}}
                     for i in range(6)]
        schemas = [
            {"@context": "https://schema.org", "@type": "Organization",
             "name": "Test", "url": "https://t.com", "description": "d",
             "telephone": "+7", "email": "a@b.com", "address": {"streetAddress": "x"},
             "openingHours": "Mon-Fri", "sameAs": [], "dateModified": "2026-01-01"},
            {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_items},
        ]
        crawl = _make_crawl(schemas=schemas)
        crawl["existing_schema"][0]["dateModified"] = "2026-01-01"
        result = calculate_score(crawl, _make_robots())
        assert result.total >= 70
        assert result.grade in ("A", "B", "C")

    def test_score_is_sum_of_breakdown(self):
        result = calculate_score(_make_crawl(), _make_robots())
        bd = result.breakdown
        assert result.total == (bd.robots_txt + bd.schema_org + bd.faq_schema +
                                bd.content_depth + bd.brand_signals + bd.freshness)
