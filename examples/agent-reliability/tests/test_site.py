"""Make sure the committed HTML preserves Medium-relevant semantic formatting."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SLUG = "the-tool-call-was-correct-the-ai-agent-was-still-wrong"


def test_medium_html_has_headings_links_and_code():
    page = (ROOT.parents[1] / "articles" / SLUG / "index.html").read_text(encoding="utf-8")
    assert "<h1>The Tool Call Was Correct." in page
    assert page.count("<h2>") >= 6
    assert '<pre><code class="language-python">' in page
    assert "&quot;" in page or "&lt;" in page or "&amp;" in page
    assert "منهنجي A-100" in page
    assert "https://github.com/faheemkhaskheli9/Sindhi-AgentBench" in page
    assert "<article>" in page and "</article>" in page


def test_html_is_fresh_against_markdown():
    completed = subprocess.run(
        [sys.executable, "tools/build_html.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
