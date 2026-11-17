"""Check that mobile Markdown avoids the structures observed to create blank Medium blocks."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
MOBILE = ROOT / "articles" / "reasoning-cache" / "medium-mobile.md"
ARTICLE = ROOT / "articles" / "reasoning-cache" / "article.md"


def test_mobile_copy_has_no_fenced_code_or_automatic_lists():
    text = MOBILE.read_text(encoding="utf-8")
    assert not re.search(r"(?m)^\s*(?:\d+[.)]|[-*+]|#{1,6}|>)\s", text)
    assert "```" not in text
    assert not re.search(r"(?m)^\s*\|", text)
    assert not re.search(r"<(?:pre|code|table|ol|li)\b", text)
    assert "\n\n\n" not in text
    assert len(text.split()) > 850


def test_mobile_copy_has_complete_links_and_examples():
    text = MOBILE.read_text(encoding="utf-8")
    assert "$121.64" in text and "$183.60" in text
    assert "python -m pytest -q" in text
    assert "https://arxiv.org/abs/2611.09891" in text
    assert "https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reasoning-cache" in text
    assert "medium-mobile.md" in ARTICLE.read_text(encoding="utf-8")
