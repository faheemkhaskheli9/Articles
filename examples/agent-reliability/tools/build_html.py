"""Regenerate the Medium HTML for this article from its Markdown source."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parents[3]
SLUG = "the-tool-call-was-correct-the-ai-agent-was-still-wrong"
SOURCE = ROOT / "articles" / SLUG / "source.md"
OUTPUT = ROOT / "articles" / SLUG / "index.html"


def regenerate(*, check: bool = False) -> None:
    md = SOURCE.read_text(encoding="utf-8")
    if not md.startswith("# "):
        raise ValueError("Article requires one H1 as its opening line")
    renderer = mistune.create_markdown(
        renderer=mistune.HTMLRenderer(escape=True),
        plugins=["strikethrough", "table", "url"],
    )
    body = renderer(md)
    if "```" in md and "<pre><code" not in body:
        raise ValueError("Markdown lost its code blocks")
    current = OUTPUT.read_text(encoding="utf-8")
    # Preserve the visual document shell and replace only semantic article markup.
    regenerated, count = re.subn(r"(?s)(<article>).*?(</article>)", lambda m: m.group(1) + body + m.group(2), current)
    if count != 1:
        raise ValueError("Expected exactly one article HTML element")
    if check:
        if regenerated != current:
            raise SystemExit("HTML is stale. Run python tools/build_html.py to refresh it.")
        print("HTML verified against Markdown source")
    else:
        OUTPUT.write_text(regenerated, encoding="utf-8")
        print(f"Updated {OUTPUT}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Medium-ready article HTML")
    parser.add_argument("--check", action="store_true", help="Fail if generated HTML differs")
    args = parser.parse_args()
    regenerate(check=args.check)


if __name__ == "__main__":
    main()
