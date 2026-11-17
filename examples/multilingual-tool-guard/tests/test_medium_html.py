"""Structural checks for the Medium import edition of this article."""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SLUG = "multilingual-tool-guard"
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
