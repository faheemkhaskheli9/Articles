"""Medium HTML remains synchronized and has no empty import blocks."""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]


class MediumTests(unittest.TestCase):
    def test_builder_matches(self):
        subprocess.run([sys.executable, str(ROOT / "tools/build_medium_html.py"),
                        "brain-model-gaps", "--check"],
                       check=True, capture_output=True, text=True)

    def test_no_empty_elements(self):
        html = (ROOT / "articles/brain-model-gaps/index.html").read_text(encoding="utf-8")
        body = html.split("<article>", 1)[1].split("</article>", 1)[0]
        self.assertEqual(body.count("<h1>"), 1)
        self.assertNotRegex(body, r"<(li|p|pre|h2|h3)>\s*</\1>")
        self.assertNotRegex(body, r"</li>\s+<li>")
        self.assertNotIn("<table", body)
        self.assertNotIn(chr(96) * 3, body)


if __name__ == "__main__":
    unittest.main()
