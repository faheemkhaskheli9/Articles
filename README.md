# Articles

Medium-importable technical articles with their complete runnable companion implementations.

## Articles

- [The Tool Call Was Correct. The AI Agent Was Still Wrong](articles/the-tool-call-was-correct-the-ai-agent-was-still-wrong/index.html) — [Runnable AI-agent evaluation companion](examples/agent-reliability/README.md)
- [Stop Making Your LLM Solve the Same Problem Twice](articles/reasoning-cache/index.html) — [Runnable Python example](examples/reasoning-cache/README.md)

## Publish the HTML to Medium

**Use the special import edition for Medium, not the full HTML tutorial.** Medium uses a third-party importer that may discard CSS and collapse multi-line <pre> code blocks. No HTML source can guarantee 1:1 reproduction in Medium. The full technical page remains intact for readers and links to the complete code.

1. In GitHub **Settings → Pages → Build and deployment**, enable **Deploy from a branch**: `main` / `/(root)` (if not already enabled).
2. Verify the Medium-specific public URL opens in a normal browser: `https://faheemkhaskheli9.github.io/Articles/articles/reasoning-cache/medium/`.
3. In **Medium's desktop web interface**, choose **Stories → Import a story** and paste this **Medium-specific URL** (not the raw GitHub source and not a local HTML file).
4. Review the imported draft. Headings, paragraphs, emphasis, lists, and links are deliberately simple; Medium still controls its rendering. Insert native **{ }** code blocks manually if you need full Python snippets within the Medium story.
5. Medium automatically associates an imported story with the original URL via canonical metadata. Decide which site should be canonical before publishing.

**Android limitation:** Medium's *Import a story* is web-only. Medium's Android app supports writing/editing but cannot reliably render pasted Markdown or HTML as rich formatted articles. Use a supported desktop browser for URL import.

The import edition intentionally includes no CSS, JavaScript, tables, or `<pre>` blocks. All runnable source, dependencies, `.env.example`, VS Code configuration and tests stay in `examples/reasoning-cache/`. The rich version of the article is still available at `articles/reasoning-cache/index.html`.

## Convention for future articles

- Each article gets `articles/<slug>/index.html` (semantic, standalone HTML; `article`, `h1`–`h3`, `p`, `pre/code`).
- Examples live in `examples/<slug>/`, with `README.md`, `requirements.txt`, `.env.example` when needed, tests, and CLI instructions.
- All additions run through CI. No credentials in Git.

The source paper is [CPU-ARC: Agentic Reasoning Caching for on-CPU Reasoning Reuse](https://arxiv.org/abs/2611.09891). The implementation is a separate, limited educational demonstration.
