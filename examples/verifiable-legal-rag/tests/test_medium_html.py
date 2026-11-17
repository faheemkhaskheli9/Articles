"""Structural checks for the Medium import edition of this article."""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SLUG = "verifiable-legal-rag"
HTML_PATH = ROOT / "articles" / SLUG / "index.html"

spec = importlib.util.spec_from_file_location("build_medium_html", ROOT / "tools" / "build_medium_html.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_committed_html_matches_markdown_source():
    builder.build(SLUG, check=True)


def test_html_avoids_patterns_that_break_medium_import():
    page = HTML_PATH.read_text(encoding="utf-8")
    body = page.split("<article>", 1)[1].split("</article>", 1)[0]
    assert not re.search(r"<li>\s*<p", body), "paragraphs inside list items"
    assert not re.search(r"</li>\s+<li>", body), "whitespace between list items"
    assert not re.search(r"<(li|p|pre|blockquote|h2|h3)>\s*</\1>", body), "empty block"
    assert "<table" not in body and "<ul>\n" not in body and "<ol>\n" not in body
    for pre in re.findall(r"<pre>(.*?)</pre>", body, flags=re.S):
        assert "\n" not in pre and "<br><br>" not in pre and pre.strip()
    outside_code = re.sub(r"<pre>.*?</pre>|<code>.*?</code>", "", body, flags=re.S)
    assert "**" not in outside_code and "`" not in outside_code
    assert body.count("<h1>") == 1
    for href in re.findall(r'href="([^"]+)"', body):
        assert href.startswith("https://")


def test_builder_rejects_loose_ordered_lists_and_empty_code():
    with pytest.raises(ValueError, match="blank lines between list items"):
        builder.convert("# T\n\n1. one\n\n2. two\n", SLUG)
    with pytest.raises(ValueError, match="Empty code block"):
        builder.convert("# T\n\n```\n\n```\n", SLUG)
    with pytest.raises(ValueError, match="Unclosed"):
        builder.convert("# T\n\n```python\nx = 1\n", SLUG)


def test_builder_escapes_and_formats_inline_markup():
    _, _, body = builder.convert("# T\n\nUse **`a<b`** and [docs](../../README.md) *now*.\n", SLUG)
    assert "<strong><code>a&lt;b</code></strong>" in body
    assert 'href="https://github.com/faheemkhaskheli9/Articles/blob/main/README.md"' in body
    assert "<em>now</em>" in body
