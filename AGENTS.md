# Article authoring rules

- **Markdown source:** Write each article as GitHub-flavored Markdown at `articles/<slug>/article.md`. This is the only file to edit by hand.
- **Medium HTML edition (always):** Every article is published on Medium by URL import, so always generate `articles/<slug>/index.html` with `python tools/build_medium_html.py <slug>` and commit it. Never paste Markdown into Medium: it produces empty numbered items, blank code blocks and single-line code. The builder emits tight lists, `<pre>` blocks with `<br>` line breaks and no empty elements; keep ordered-list items on consecutive lines and avoid tables.
- **General titles:** Title each article for the broader engineering problem (for example RAG reliability, agent evaluation, inference cost), not for one project or domain. Use a project-specific title only for an article in a series. The project can appear in the subtitle and body.
- Markdown is the canonical source for the article. Retain legacy HTML URLs for compatibility, but do not use those files as editable article sources.
- Each AI article should focus on practical coding: the problem, use cases, a worked scenario, step-by-step implementation, runnable examples, tests, adversarial cases, expert considerations, and credible citations.
- Maintain a complete, runnable companion project under `examples/<slug>/`: source code, `requirements.txt`, `pyproject.toml`, `.env.example`, `.vscode/launch.json` (plus entries in the root `.vscode/launch.json`), README with setup steps, tests and a GitHub Actions workflow.
- Check examples against real repository behavior, run relevant tests, and keep Git history clear. Do not invent benchmark figures or test results.
- GitHub renders Markdown; Medium mobile may not. Never imply a pasted Markdown article automatically becomes formatted on Medium Android.
- Add a test that runs `build_medium_html.py <slug> --check` and checks the HTML structure (see `examples/verifiable-legal-rag/tests/test_medium_html.py`). `medium-mobile.md` files are legacy and not required for new articles.
