"""The reasoning-cache article must be usable GitHub-flavored Markdown."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
ARTICLE = ROOT / "articles" / "reasoning-cache" / "article.md"


def test_markdown_article_is_complete():
    content = ARTICLE.read_text(encoding="utf-8")
    prose = re.sub(r"(?ms)^\x60\x60\x60.*?^\x60\x60\x60[ \t]*$", "", content)
    assert len(re.findall(r"^# ", prose, flags=re.M)) == 1
    assert len(re.findall(r"^## ", prose, flags=re.M)) >= 7
    assert len(re.findall(r"^\x60\x60\x60", content, flags=re.M)) >= 12
    assert "CURATED_STEPS" in content
    assert "python -m pytest -q" in content
    assert "$121.64" in content and "$183.60" in content
    assert "https://arxiv.org/abs/2611.09891" in content
    assert "https://github.com/faheemkhaskheli9/Articles/tree/main/examples/reasoning-cache" in content
    assert "<article" not in content and "<style" not in content


def test_repository_markdown_convention():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Markdown is the source of truth" in readme
    assert "Markdown only" in agents
    assert "reasoning-cache/article.md" in readme
