"""
robots.txt audit — checks which AI bots are blocked/allowed.
Standalone version for CLI (mirrors backend/app/core/robots.py).
"""
import httpx
from dataclasses import dataclass, field
from urllib.robotparser import RobotFileParser


AI_BOTS: dict[str, str] = {
    "GPTBot": "ChatGPT (OpenAI)",
    "ClaudeBot": "Claude (Anthropic)",
    "anthropic-ai": "Anthropic crawler",
    "PerplexityBot": "Perplexity AI",
    "CCBot": "Common Crawl",
    "Google-Extended": "Google AI training",
    "Bytespider": "ByteDance / TikTok AI",
    "YouBot": "You.com",
    "cohere-ai": "Cohere",
    "ia_archiver": "Internet Archive",
}


@dataclass
class RobotsAudit:
    has_robots_txt: bool
    blocked_bots: list[str] = field(default_factory=list)
    allowed_bots: list[str] = field(default_factory=list)
    ai_blocking_score: int = 0   # 0-100, 100 = all blocked
    issues: list[str] = field(default_factory=list)


async def audit_robots(base_url: str) -> RobotsAudit:
    robots_txt = await _fetch_robots(base_url)

    if not robots_txt:
        return RobotsAudit(
            has_robots_txt=False,
            allowed_bots=list(AI_BOTS.keys()),
            ai_blocking_score=0,
        )

    parser = _build_parser(base_url, robots_txt)
    blocked, allowed = _check_bots(parser)
    blocking_score = int(len(blocked) / len(AI_BOTS) * 100) if AI_BOTS else 0

    return RobotsAudit(
        has_robots_txt=True,
        blocked_bots=blocked,
        allowed_bots=allowed,
        ai_blocking_score=blocking_score,
        issues=[f"{AI_BOTS[b]} ({b}) blocked" for b in blocked],
    )


def _build_parser(base_url: str, robots_txt: str) -> RobotFileParser:
    parser = RobotFileParser(url=base_url.rstrip("/") + "/robots.txt")
    parser.parse(robots_txt.splitlines())
    return parser


def _check_bots(parser: RobotFileParser) -> tuple[list[str], list[str]]:
    blocked, allowed = [], []
    for bot in AI_BOTS:
        (allowed if parser.can_fetch(bot, "/") else blocked).append(bot)
    return blocked, allowed


async def _fetch_robots(base_url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(base_url.rstrip("/") + "/robots.txt")
            if resp.status_code == 200:
                return resp.text
    except Exception:
        pass
    return None
