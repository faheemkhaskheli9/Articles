# Articles

Medium-importable technical articles with their complete runnable companion implementations.

## Articles

- [The Tool Call Was Correct. The AI Agent Was Still Wrong](articles/the-tool-call-was-correct-the-ai-agent-was-still-wrong/index.html) — [Runnable AI-agent evaluation companion](examples/agent-reliability/README.md)
- [Stop Making Your LLM Solve the Same Problem Twice](articles/reasoning-cache/index.html) — [Runnable Python example](examples/reasoning-cache/README.md)

## Publish the HTML to Medium

**Important:** Medium's *Import a story* accepts a **public URL**, not a downloaded `.html` file, GitHub source URL, or raw Markdown. It is **web-only**, not in the Medium Android app.

1. On GitHub, open **Settings → Pages → Build and deployment**.
2. Choose **Deploy from a branch**, `main`, `/(root)`, then save. (Repository owner must enable Pages; initial publication can take time.)
3. Open the public article URL: `https://faheemkhaskheli9.github.io/Articles/articles/reasoning-cache/`.
4. On **Medium's web interface**, open **Stories → Import a story** and enter that URL.
5. Review headings, code blocks, image embeds and links in the imported draft. Correct anything Medium's import converter changed; publish when ready.

Medium sets an automatic canonical link pointing to the original GitHub Pages article after import. For SEO, decide whether GitHub Pages or Medium should be your primary destination before publishing. The conversion is not guaranteed to retain every code block or diagram.

## Convention for future articles

- Each article gets `articles/<slug>/index.html` (semantic, standalone HTML; `article`, `h1`–`h3`, `p`, `pre/code`).
- Examples live in `examples/<slug>/`, with `README.md`, `requirements.txt`, `.env.example` when needed, tests, and CLI instructions.
- All additions run through CI. No credentials in Git.

The source paper is [CPU-ARC: Agentic Reasoning Caching for on-CPU Reasoning Reuse](https://arxiv.org/abs/2611.09891). The implementation is a separate, limited educational demonstration.
