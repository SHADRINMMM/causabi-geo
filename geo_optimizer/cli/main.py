"""
geo-optimizer CLI — analyze and fix your website's AI readiness.

Usage:
    geo-optimizer analyze https://yoursite.com
    geo-optimizer fix https://yoursite.com --output ./fixes
    geo-optimizer score https://yoursite.com --json
"""
import asyncio
import json
import sys
from pathlib import Path

import click

from geo_optimizer.cli.output import console, print_score, print_fix_done, spinner


@click.group()
@click.version_option(package_name="causabi-geo")
def cli() -> None:
    """Fix how AI search engines see your website."""


@cli.command()
@click.argument("url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def analyze(url: str, as_json: bool) -> None:
    """Analyze a website's AI readiness and show score."""
    result = asyncio.run(_run_analyze(url))
    if not result:
        sys.exit(1)

    crawl, robots, score = result

    if as_json:
        click.echo(json.dumps(score.to_dict(), indent=2, ensure_ascii=False))
        return

    print_score(url, score)


@cli.command()
@click.argument("url")
@click.option("--output", "-o", default="./geo-fixes", show_default=True,
              help="Directory to save fix files")
@click.option("--api-key", envvar="GEMINI_API_KEY",
              help="Gemini API key for FAQ generation (or set GEMINI_API_KEY)")
def fix(url: str, output: str, api_key: str | None) -> None:
    """Generate fix files for a website (robots.txt patch, Schema JSON, llms.txt)."""
    result = asyncio.run(_run_fix(url, output, api_key))
    if not result:
        sys.exit(1)


@cli.command()
@click.argument("url")
def score(url: str) -> None:
    """Quick score check — alias for analyze."""
    ctx = click.get_current_context()
    ctx.invoke(analyze, url=url, as_json=False)


# --- Async runners ---

async def _run_analyze(url: str):
    from geo_optimizer.core.crawler import crawl_site
    from geo_optimizer.core.robots import audit_robots
    from geo_optimizer.core.scorer import calculate_score

    with spinner(f"Crawling {url}...") as p:
        p.add_task("crawl")
        crawl = await crawl_site(url)

    if not crawl.ok:
        console.print(f"[red]Failed to crawl {url}: {crawl.error}[/red]")
        return None

    with spinner("Auditing robots.txt...") as p:
        p.add_task("robots")
        robots = await audit_robots(url)

    crawl_dict = {
        "existing_schema": crawl.existing_schema,
        "body_text": crawl.body_text,
        "pages": crawl.pages,
        "business_name": crawl.business_name,
        "phone": crawl.phone,
        "email": crawl.email,
        "address": crawl.address,
        "social": crawl.social,
    }
    score_result = calculate_score(crawl_dict, robots)
    return crawl, robots, score_result


async def _run_fix(url: str, output_dir: str, api_key: str | None) -> bool:
    from geo_optimizer.core.crawler import crawl_site
    from geo_optimizer.core.robots import audit_robots
    from geo_optimizer.core.scorer import calculate_score

    with spinner(f"Analyzing {url}...") as p:
        p.add_task("analyze")
        crawl = await crawl_site(url)
        if not crawl.ok:
            console.print(f"[red]Failed to crawl {url}: {crawl.error}[/red]")
            return False
        robots = await audit_robots(url)

    crawl_dict = {
        "existing_schema": crawl.existing_schema,
        "body_text": crawl.body_text,
        "pages": crawl.pages,
        "business_name": crawl.business_name,
        "phone": crawl.phone,
        "email": crawl.email,
        "address": crawl.address,
        "social": crawl.social,
    }
    score_result = calculate_score(crawl_dict, robots)

    print_score(url, score_result)

    # Generate fix files
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved = []

    with spinner("Generating fix files...") as p:
        p.add_task("generate")
        files = await _generate_fixes(url, crawl, robots, api_key)

    for filename, content in files.items():
        path = out / filename
        path.write_text(content, encoding="utf-8")
        saved.append(filename)

    print_fix_done(output_dir, saved)
    return True


async def _generate_fixes(url: str, crawl, robots, api_key: str | None) -> dict[str, str]:
    from geo_optimizer.generators.robots import patch_robots
    from geo_optimizer.generators.schema import generate_organization_schema
    from geo_optimizer.generators.llms_txt import generate_llms_txt

    files = {}

    # 1. robots.txt patch
    robots_patched = await patch_robots(url)
    files["robots.txt"] = robots_patched

    # 2. Organization schema
    schema_json = generate_organization_schema(crawl)
    files["schema.json"] = schema_json

    # 3. llms.txt
    llms = generate_llms_txt(crawl)
    files["llms.txt"] = llms

    # 4. FAQ schema (requires Gemini API key)
    if api_key:
        try:
            from geo_optimizer.generators.faq import generate_faq_schema
            faq_json = await generate_faq_schema(crawl, api_key)
            files["faq-schema.json"] = faq_json
        except Exception as e:
            console.print(f"[yellow]FAQ generation skipped: {e}[/yellow]")

    # 5. README with instructions
    files["HOW-TO-APPLY.md"] = _how_to_apply(files)

    return files


def _how_to_apply(files: dict) -> str:
    lines = ["# How to Apply GEO Fixes\n"]
    if "robots.txt" in files:
        lines.append("## 1. robots.txt\nReplace your `/robots.txt` with the provided file.\n")
    if "schema.json" in files:
        lines.append("## 2. Schema.org\nAdd to your `<head>`:\n```html\n<script type=\"application/ld+json\">\n<!-- paste contents of schema.json -->\n</script>\n```\n")
    if "faq-schema.json" in files:
        lines.append("## 3. FAQ Schema\nAdd to your homepage `<head>` (same way as schema.json).\n")
    if "llms.txt" in files:
        lines.append("## 4. llms.txt\nUpload to your website root: `yoursite.com/llms.txt`\n")
    lines.append("\nGenerated by [geo-optimizer](https://causabi.com)")
    return "\n".join(lines)
