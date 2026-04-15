"""Tests for SVG badge generation (standalone, mirrors backend/app/api/v1/badge.py)."""
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# --- Inline duplicates of badge helper functions for unit testing ---

_CHAR_W: dict[str, int] = {c: 7 for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
_CHAR_W.update({"/": 5, " ": 4, ":": 4, ".": 4, "-": 5})


def _text_width(s: str, pad: int = 10) -> int:
    return sum(_CHAR_W.get(c, 7) for c in s) + pad


def _score_color(score: int) -> str:
    if score >= 80:
        return "#4CAF50"
    if score >= 60:
        return "#FF9800"
    if score >= 40:
        return "#FF5722"
    return "#9E9E9E"


def _generate_svg(domain: str, score: int) -> str:
    label = "GEO Score"
    value = f"{score}/100"
    lw = _text_width(label)
    rw = _text_width(value)
    total = lw + rw
    color = _score_color(score)
    lx = lw // 2 + 1
    rx = lw + rw // 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20">'
        f'<rect width="{lw}" height="20" fill="#555"/>'
        f'<rect x="{lw}" width="{rw}" height="20" fill="{color}"/>'
        f'<text x="{lx}" y="14">{label}</text>'
        f'<text x="{rx}" y="14">{value}</text>'
        f"</svg>"
    )


def _normalize_domain(raw: str) -> str:
    raw = raw.strip().lower()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return urlparse(raw).netloc.replace("www.", "")


# --- Tests ---

class TestScoreColor:
    def test_green_at_80(self):
        assert _score_color(80) == "#4CAF50"
        assert _score_color(100) == "#4CAF50"

    def test_orange_at_60(self):
        assert _score_color(60) == "#FF9800"
        assert _score_color(79) == "#FF9800"

    def test_red_at_40(self):
        assert _score_color(40) == "#FF5722"
        assert _score_color(59) == "#FF5722"

    def test_grey_below_40(self):
        assert _score_color(0) == "#9E9E9E"
        assert _score_color(39) == "#9E9E9E"


class TestGenerateSvg:
    def test_returns_valid_xml(self):
        svg = _generate_svg("example.com", 75)
        root = ET.fromstring(svg)
        assert root.tag in ("svg", "{http://www.w3.org/2000/svg}svg")

    def test_contains_score(self):
        svg = _generate_svg("example.com", 75)
        assert "75/100" in svg

    def test_contains_label(self):
        svg = _generate_svg("example.com", 75)
        assert "GEO Score" in svg

    def test_green_color_for_high_score(self):
        svg = _generate_svg("example.com", 90)
        assert "#4CAF50" in svg

    def test_grey_color_for_low_score(self):
        svg = _generate_svg("example.com", 10)
        assert "#9E9E9E" in svg

    def test_orange_color_for_mid_score(self):
        svg = _generate_svg("example.com", 65)
        assert "#FF9800" in svg


class TestNormalizeDomain:
    def test_strips_www(self):
        assert _normalize_domain("www.example.com") == "example.com"

    def test_handles_https(self):
        assert _normalize_domain("https://example.com") == "example.com"

    def test_handles_bare_domain(self):
        assert _normalize_domain("example.com") == "example.com"

    def test_lowercases(self):
        assert _normalize_domain("EXAMPLE.COM") == "example.com"
