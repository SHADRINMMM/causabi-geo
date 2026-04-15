"""
Rich terminal output for geo-optimizer CLI.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from geo_optimizer.core.scorer import ScoreResult

console = Console()

SEVERITY_ICONS = {"critical": "❌", "warning": "⚠️ ", "info": "ℹ️ "}
SEVERITY_COLORS = {"critical": "red", "warning": "yellow", "info": "blue"}

GRADE_COLORS = {"A": "bright_green", "B": "green", "C": "yellow", "D": "orange3", "F": "red"}

CATEGORY_LABELS = {
    "robots_txt":    ("robots.txt",    20),
    "schema_org":    ("Schema.org",    25),
    "faq_schema":    ("FAQ Schema",    20),
    "content_depth": ("Content",       15),
    "brand_signals": ("Brand / NAP",   10),
    "freshness":     ("Freshness",     10),
}


def print_score(url: str, result: ScoreResult) -> None:
    grade_color = GRADE_COLORS.get(result.grade, "white")

    # Header panel
    score_bar = _score_bar(result.total, 100, width=30)
    console.print(Panel(
        f"  [bold]{url}[/bold]\n\n"
        f"  AI Readiness Score: [{grade_color} bold]{result.total}/100  Grade {result.grade}[/{grade_color} bold]\n"
        f"  {score_bar}",
        title="[bold]GEO Optimizer[/bold]",
        border_style=grade_color,
        padding=(1, 2),
    ))

    # Breakdown table
    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("Category", style="dim", width=16)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Max", justify="right", width=5)
    table.add_column("", width=22)  # bar

    breakdown_dict = result.breakdown.__dict__
    for key, (label, max_val) in CATEGORY_LABELS.items():
        val = breakdown_dict.get(key, 0)
        bar = _score_bar(val, max_val, width=18)
        color = "green" if val == max_val else ("yellow" if val >= max_val * 0.5 else "red")
        table.add_row(label, f"[{color}]{val}[/{color}]", str(max_val), bar)

    console.print(table)

    # Issues
    if result.issues:
        console.print("\n[bold]Issues to fix:[/bold]")
        for issue in result.issues:
            icon = SEVERITY_ICONS.get(issue.severity, "•")
            color = SEVERITY_COLORS.get(issue.severity, "white")
            console.print(f"  {icon} [{color}]{issue.message}[/{color}]")
            console.print(f"     [dim]→ {issue.fix}[/dim]")
    else:
        console.print("\n  [green]✅ No critical issues found![/green]")

    # CTA
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace("www.", "") or url
    console.print(f"\n  [dim]Run fixes:[/dim]  geo-optimizer fix {url}")
    console.print(f"  [dim]Share:[/dim]      https://causabi.com/score/{domain}\n")


def print_fix_done(output_dir: str, files: list[str]) -> None:
    console.print(f"\n[green]✅ Fix files saved to:[/green] [bold]{output_dir}/[/bold]")
    for f in files:
        console.print(f"   • {f}")
    console.print("\n[dim]Upload these files to your website root to apply fixes.[/dim]\n")


def spinner(message: str) -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[dim]{message}[/dim]"),
        console=console,
        transient=True,
    )


def _score_bar(val: int, max_val: int, width: int = 20) -> str:
    ratio = val / max_val if max_val else 0
    filled = int(ratio * width)
    empty = width - filled
    color = "green" if ratio >= 0.8 else ("yellow" if ratio >= 0.5 else "red")
    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"
