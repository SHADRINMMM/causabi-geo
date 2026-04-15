"""
AI Readiness Score (0-100).
Standalone version for CLI (mirrors backend/app/core/scorer.py).
"""
from dataclasses import dataclass, asdict
from geo_optimizer.core.robots import RobotsAudit


@dataclass
class ScoreBreakdown:
    robots_txt: int     # 0-20
    schema_org: int     # 0-25
    faq_schema: int     # 0-20
    content_depth: int  # 0-15
    brand_signals: int  # 0-10
    freshness: int      # 0-10


@dataclass
class ScoreIssue:
    category: str
    severity: str   # "critical" | "warning" | "info"
    message: str
    fix: str


@dataclass
class ScoreResult:
    total: int
    breakdown: ScoreBreakdown
    issues: list[ScoreIssue]
    grade: str

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "grade": self.grade,
            "breakdown": asdict(self.breakdown),
            "issues": [asdict(i) for i in self.issues],
        }


def calculate_score(crawl_data: dict, robots_audit: RobotsAudit) -> ScoreResult:
    issues: list[ScoreIssue] = []
    breakdown = ScoreBreakdown(
        robots_txt=_score_robots(robots_audit, issues),
        schema_org=_score_schema(crawl_data, issues),
        faq_schema=_score_faq(crawl_data, issues),
        content_depth=_score_content(crawl_data, issues),
        brand_signals=_score_brand(crawl_data, issues),
        freshness=_score_freshness(crawl_data, issues),
    )
    total = sum(asdict(breakdown).values())
    return ScoreResult(total=total, breakdown=breakdown, issues=issues, grade=_grade(total))


def _score_robots(audit: RobotsAudit, issues: list[ScoreIssue]) -> int:
    if not audit.has_robots_txt or not audit.blocked_bots:
        return 20
    score = max(0, 20 - len(audit.blocked_bots) * 3)
    for bot in audit.blocked_bots[:3]:
        issues.append(ScoreIssue(
            category="robots_txt", severity="critical",
            message=f"{bot} is blocked from crawling your site",
            fix=f"Add 'User-agent: {bot}\\nAllow: /' to your robots.txt",
        ))
    if len(audit.blocked_bots) > 3:
        issues.append(ScoreIssue(
            category="robots_txt", severity="critical",
            message=f"{len(audit.blocked_bots) - 3} more AI bots are blocked",
            fix="Run: geo-optimizer fix <url> to auto-patch your robots.txt",
        ))
    return score


def _score_schema(crawl_data: dict, issues: list[ScoreIssue]) -> int:
    schemas = crawl_data.get("existing_schema", [])
    if not schemas:
        issues.append(ScoreIssue(
            category="schema_org", severity="critical",
            message="No Schema.org markup found",
            fix="Add Organization or LocalBusiness JSON-LD to your homepage",
        ))
        return 0

    types = {_schema_type(s) for s in schemas}
    org_types = {"Organization", "LocalBusiness", "Store", "Restaurant",
                 "MedicalClinic", "Hotel", "BeautySalon", "SportsActivityLocation"}
    digital_types = {"SoftwareApplication", "WebSite", "WebApplication", "Service"}
    has_org = bool(types & org_types)
    has_digital = bool(types & digital_types)

    if not has_org and not has_digital:
        issues.append(ScoreIssue(
            category="schema_org", severity="warning",
            message="No Organization, LocalBusiness, or SoftwareApplication schema found",
            fix="Add Organization JSON-LD with name, description, url, telephone",
        ))
        return 5

    if has_org:
        main = next((s for s in schemas if _schema_type(s) in org_types), schemas[0])
        rich_keys = ["description", "telephone", "email", "address",
                     "openingHours", "sameAs", "aggregateRating"]
    else:
        main = next((s for s in schemas if _schema_type(s) in digital_types), schemas[0])
        rich_keys = ["description", "url", "offers", "featureList",
                     "publisher", "dateModified", "sameAs"]

    attr_count = sum(1 for k in rich_keys if main.get(k))
    return min(25, 15 + attr_count * 2)


def _score_faq(crawl_data: dict, issues: list[ScoreIssue]) -> int:
    schemas = crawl_data.get("existing_schema", [])
    if "FAQPage" not in {_schema_type(s) for s in schemas}:
        issues.append(ScoreIssue(
            category="faq_schema", severity="critical",
            message="No FAQPage schema — citation rate is 41% lower without it",
            fix="Generate FAQPage JSON-LD with 5+ Q&A pairs",
        ))
        return 0
    faq = next(s for s in schemas if _schema_type(s) == "FAQPage")
    count = len(faq.get("mainEntity", []))
    if count < 3:
        issues.append(ScoreIssue(
            category="faq_schema", severity="warning",
            message=f"Only {count} FAQ item(s) — minimum 3 for citation impact",
            fix="Add at least 3-7 FAQ pairs covering services, prices, differentiators",
        ))
        return 10
    return min(20, 10 + count * 2)


def _score_content(crawl_data: dict, issues: list[ScoreIssue]) -> int:
    text = crawl_data.get("body_text", "")
    pages = crawl_data.get("pages", [])
    words = len(text.split()) if text else sum(
        len((p.get("body_text") or "").split()) for p in pages
    )
    if words < 200:
        issues.append(ScoreIssue(
            category="content_depth", severity="critical",
            message=f"Very thin content ({words} words)",
            fix="Add detailed service/product descriptions (500+ words total)",
        ))
        return 3
    if words < 500:
        issues.append(ScoreIssue(
            category="content_depth", severity="warning",
            message=f"Thin content ({words} words) — AI has little to cite",
            fix="Expand content to 500+ words across your pages",
        ))
        return 8
    return 15


def _score_brand(crawl_data: dict, issues: list[ScoreIssue]) -> int:
    score = 0
    missing = []
    if crawl_data.get("business_name"):
        score += 3
    else:
        missing.append("business name")
    if crawl_data.get("phone"):
        score += 3
    else:
        missing.append("phone")
    if crawl_data.get("address"):
        score += 2
    else:
        missing.append("address")
    if crawl_data.get("email"):
        score += 1
    if crawl_data.get("social"):
        score += 1
    if missing:
        issues.append(ScoreIssue(
            category="brand_signals", severity="warning",
            message=f"Missing NAP signals: {', '.join(missing)}",
            fix="Add Name, Address, Phone prominently on homepage and contact page",
        ))
    return min(10, score)


def _score_freshness(crawl_data: dict, issues: list[ScoreIssue]) -> int:
    for s in crawl_data.get("existing_schema", []):
        if s.get("dateModified") or s.get("datePublished"):
            return 10
    text = (crawl_data.get("body_text") or "").lower()
    if any(y in text for y in ["2025", "2026"]):
        return 7
    issues.append(ScoreIssue(
        category="freshness", severity="info",
        message="No content freshness signals detected",
        fix="Add dateModified to Schema.org markup or show last-updated dates",
    ))
    return 0


def _schema_type(s: dict) -> str:
    t = s.get("@type", "")
    return (t[0] if isinstance(t, list) and t else str(t))


def _grade(total: int) -> str:
    if total >= 85:
        return "A"
    if total >= 70:
        return "B"
    if total >= 50:
        return "C"
    if total >= 30:
        return "D"
    return "F"
