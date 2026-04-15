"""Tests for robots.txt audit."""
import pytest
from unittest.mock import AsyncMock, patch
from geo_optimizer.core.robots import audit_robots, _build_parser, _check_bots, AI_BOTS


BLOCKED_ROBOTS = """
User-agent: *
Disallow: /

User-agent: Googlebot
Allow: /
"""

OPEN_ROBOTS = """
User-agent: *
Allow: /
"""

PARTIAL_ROBOTS = """
User-agent: GPTBot
Disallow: /

User-agent: *
Allow: /
"""


class TestCheckBots:
    def test_open_robots_allows_all(self):
        parser = _build_parser("https://test.com", OPEN_ROBOTS)
        blocked, allowed = _check_bots(parser)
        assert "GPTBot" in allowed
        assert "ClaudeBot" in allowed
        assert len(blocked) == 0

    def test_blocked_robots_blocks_ai(self):
        parser = _build_parser("https://test.com", BLOCKED_ROBOTS)
        blocked, allowed = _check_bots(parser)
        assert "GPTBot" in blocked
        assert "ClaudeBot" in blocked

    def test_partial_block(self):
        parser = _build_parser("https://test.com", PARTIAL_ROBOTS)
        blocked, allowed = _check_bots(parser)
        assert "GPTBot" in blocked
        assert "ClaudeBot" in allowed


class TestAuditRobots:
    @pytest.mark.asyncio
    async def test_no_robots_txt_full_allowed(self):
        with patch("geo_optimizer.core.robots._fetch_robots", AsyncMock(return_value=None)):
            result = await audit_robots("https://example.com")
        assert not result.has_robots_txt
        assert result.ai_blocking_score == 0
        assert len(result.allowed_bots) == len(AI_BOTS)

    @pytest.mark.asyncio
    async def test_open_site_no_blocked(self):
        with patch("geo_optimizer.core.robots._fetch_robots", AsyncMock(return_value=OPEN_ROBOTS)):
            result = await audit_robots("https://example.com")
        assert result.has_robots_txt
        assert len(result.blocked_bots) == 0
        assert result.ai_blocking_score == 0

    @pytest.mark.asyncio
    async def test_partial_block_correct_score(self):
        with patch("geo_optimizer.core.robots._fetch_robots", AsyncMock(return_value=PARTIAL_ROBOTS)):
            result = await audit_robots("https://example.com")
        assert "GPTBot" in result.blocked_bots
        assert result.ai_blocking_score > 0
        assert len(result.issues) > 0
