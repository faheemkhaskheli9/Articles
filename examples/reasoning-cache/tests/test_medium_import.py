"""Check the Medium import edition avoids HTML that Medium commonly strips.

These tests are structural only; they do not simulate Medium's third-party importer.
"""
from html.parser import HTMLParser
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "articles" / "reasoning-cache" / "medium" / "index.html"
ALLOWED = {
    "html", "head", "meta", "title", "link", "body",
    "article", "h1", "h2", "p", "a", "strong", "em",
    "blockquote", "ul", "ol", "li",
}
FORBIDDEN = {"style", "script", "pre", "code", "table", "img", "iframe", "svg"}


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "a":
            self.links.extend(v for k, v in attrs if k == "href")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def test_import_edition_has_basic_semantic_structure():
    text = SOURCE.read_text(encoding="utf-8")
    parser = TagCollector()
    parser.feed(text)
    tags = set(parser.tags)
    assert not (tags & FORBIDDEN)
    assert tags <= ALLOWED, tags - ALLOWED
    assert parser.tags.count("h1") == 1
    assert parser.tags.count("h2") >= 7
    assert parser.tags.count("article") == 1
    assert parser.tags.count("a") >= 5
    assert "183.60" in text and "121.64" in text


def test_import_edition_links_to_complete_code():
    parser = TagCollector()
    parser.feed(SOURCE.read_text(encoding="utf-8"))
    assert all(url.startswith("https://") for url in parser.links)
    assert any(
        "github.com/faheemkhaskheli9/Articles/tree/main/examples/reasoning-cache" in url
        for url in parser.links
    )
    assert any("arxiv.org/abs/2611.09891" in url for url in parser.links)
