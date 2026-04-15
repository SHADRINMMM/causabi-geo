"""
robots.txt patcher — adds AI bot allow rules to existing robots.txt.
"""
import httpx

AI_BOTS = [
    "GPTBot", "ClaudeBot", "anthropic-ai", "PerplexityBot",
    "CCBot", "Google-Extended", "Bytespider", "YouBot",
    "cohere-ai", "ia_archiver",
]


async def patch_robots(base_url: str) -> str:
    """Fetch existing robots.txt and patch with AI bot permissions."""
    existing = await _fetch(base_url)
    return _patch(existing, base_url)


def _patch(existing: str, base_url: str) -> str:
    existing_lower = existing.lower()
    llms_url = base_url.rstrip("/") + "/llms.txt"
    additions = []

    for bot in AI_BOTS:
        if bot.lower() not in existing_lower:
            additions.append(f"\n# {bot} — AI search engine crawler")
            additions.append(f"User-agent: {bot}")
            additions.append("Allow: /")
            additions.append("")

    if "llms.txt" not in existing_lower:
        additions.append("# AI-readable site description")
        additions.append(f"# llms.txt: {llms_url}")
        additions.append("")

    if not additions:
        return existing

    parts = [existing.strip()] if existing.strip() else []
    parts.append("\n# === AI Search Engine Optimization (geo-optimizer) ===")
    parts.extend(additions)
    return "\n".join(parts)


async def _fetch(base_url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(base_url.rstrip("/") + "/robots.txt")
            if resp.status_code == 200:
                return resp.text
    except Exception:
        pass
    return ""
