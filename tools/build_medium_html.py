"""Build a Medium-importable HTML edition from articles/<slug>/article.md.

Medium's importer (medium.com/p/import) reads a public URL, such as the GitHub
Pages copy of articles/<slug>/index.html. Pasted Markdown, and HTML produced by
generic Markdown renderers, can leave empty numbered items, blank code blocks and
code collapsed onto one line. This builder emits a deliberately small HTML subset:

* lists on one line, <li> with inline content only (no <p>, no whitespace nodes)
* one <pre> per code block, lines joined with <br>, never empty
* no tables, no nested blocks, no empty elements
* relative links rewritten to absolute GitHub URLs

Standard library only. Supported Markdown: #/##/### headings, paragraphs,
"1." and "-" lists, fenced code, "> " blockquotes, **bold**, *italic*,
`code` and [links](url).
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/faheemkhaskheli9/Articles"
PAGES_URL = "https://faheemkhaskheli9.github.io/Articles"

_LIST_RE = re.compile(r"^(?:(\d+)\.|[-*])\s+(.*)$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def absolute_url(url: str, slug: str) -> str:
    if re.match(r"^[a-z]+:", url) or url.startswith("#"):
        return url
    base = (ROOT / "articles" / slug).resolve()
    target = (base / url).resolve().relative_to(ROOT).as_posix()
    kind = "tree" if not Path(target).suffix else "blob"
    return f"{REPO_URL}/{kind}/main/{target}"


def inline(text: str, slug: str) -> str:
    """Escape text, then apply code, links, bold and italic without touching code spans."""
    tokens: list[str] = []

    def stash(markup: str) -> str:
        tokens.append(markup)
        return f"\x00{len(tokens) - 1}\x00"

    def keep_link(m: re.Match) -> str:
        href = html.escape(absolute_url(m.group(2), slug), quote=True)
        label = re.sub(r"`([^`]+)`", r"\1", m.group(1))
        return stash(f'<a href="{href}">{html.escape(label, quote=False)}</a>')

    text = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{html.escape(m.group(1), quote=False)}</code>"), text)
    text = _LINK_RE.sub(keep_link, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], text)
    return text


def convert(markdown: str, slug: str) -> tuple[str, str, str]:
    """Return (title, description, body_html)."""
    lines = markdown.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Article must start with a single '# ' title line")
    title = lines[0][2:].strip()
    description = ""
    blocks: list[str] = []
    i = 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("```"):
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            if i == len(lines):
                raise ValueError("Unclosed code fence")
            i += 1
            # Blank lines inside <pre> render as empty gaps on Medium; drop them.
            code = [c for c in code if c.strip()]
            if not code:
                raise ValueError("Empty code block")
            blocks.append("<pre>" + "<br>".join(html.escape(c, quote=False) for c in code) + "</pre>")
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            if level == 1:
                raise ValueError("Only one '# ' title is allowed")
            text = stripped[level:].strip()
            tag = "h2" if level == 2 else "h3"
            blocks.append(f"<{tag}>{inline(text, slug)}</{tag}>")
            i += 1
            continue
        if stripped.startswith(">"):
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            text = " ".join(q for q in quote if q)
            blocks.append(f"<blockquote>{inline(text, slug)}</blockquote>")
            continue
        list_match = _LIST_RE.match(stripped)
        if list_match:
            ordered = list_match.group(1) is not None
            if ordered and list_match.group(1) != "1":
                raise ValueError(
                    f"Line {i + 1}: ordered list starts at {list_match.group(1)}; "
                    "remove blank lines between list items so Medium keeps one list"
                )
            items: list[str] = []
            while i < len(lines):
                m = _LIST_RE.match(lines[i].strip())
                if not m or (m.group(1) is not None) != ordered:
                    break
                items.append(m.group(2).strip())
                i += 1
            if any(not item for item in items):
                raise ValueError("Empty list item")
            tag = "ol" if ordered else "ul"
            blocks.append(f"<{tag}>" + "".join(f"<li>{inline(t, slug)}</li>" for t in items) + f"</{tag}>")
            continue
        para: list[str] = []
        while i < len(lines):
            s = lines[i].strip()
            if not s or s.startswith(("```", "#", ">")) or _LIST_RE.match(s):
                break
            para.append(s)
            i += 1
        text = " ".join(para)
        if not description and not text.startswith("*"):
            description = re.sub(r"[*`\[\]]|\([^)]*\)", "", text)[:200]
        blocks.append(f"<p>{inline(text, slug)}</p>")
    return title, description, "\n".join(blocks)


def render(markdown: str, slug: str) -> str:
    title, description, body = convert(markdown, slug)
    esc = lambda s: html.escape(s, quote=True)  # noqa: E731
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="author" content="Faheem Khaskheli">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<link rel="canonical" href="{PAGES_URL}/articles/{slug}/">
<!-- Generated from article.md by tools/build_medium_html.py. Do not edit by hand. -->
</head>
<body>
<article>
<h1>{esc(title)}</h1>
{body}
</article>
</body>
</html>
"""


def build(slug: str, *, check: bool = False) -> Path:
    source = ROOT / "articles" / slug / "article.md"
    output = ROOT / "articles" / slug / "index.html"
    result = render(source.read_text(encoding="utf-8"), slug)
    if check:
        if not output.exists() or output.read_text(encoding="utf-8") != result:
            raise SystemExit(f"{output.relative_to(ROOT)} is stale. Run: python tools/build_medium_html.py {slug}")
        print(f"{output.relative_to(ROOT)} matches article.md")
    else:
        output.write_text(result, encoding="utf-8")
        print(f"Wrote {output.relative_to(ROOT)}")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug", help="folder name under articles/")
    parser.add_argument("--check", action="store_true", help="fail if index.html is out of date")
    args = parser.parse_args(argv)
    build(args.slug, check=args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
