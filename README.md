# Articles

Implementation-first AI engineering articles in **Markdown**, accompanied by complete runnable projects.

## Articles

- [Stop Making Your LLM Solve the Same Problem Twice](articles/reasoning-cache/article.md) — [Reasoning-cache Python example](examples/reasoning-cache/README.md)
- [The Tool Call Was Correct. The AI Agent Was Still Wrong](articles/the-tool-call-was-correct-the-ai-agent-was-still-wrong/source.md) — [Agent evaluation example](examples/agent-reliability/README.md)

## Article format: Markdown is the source of truth

**All future articles and substantial revisions must be committed as Markdown (.md), not HTML.** Use `articles/<slug>/article.md` for new articles. Older HTML files remain available only to avoid breaking existing URLs; they are not the editable article source.

- Use GitHub-flavored Markdown headings, links, numbered steps, and fenced, language-labeled code blocks.
- Prioritize practical implementation: when to use the technique, a realistic scenario, working code, validation, testing, expert tradeoffs, and documented limitations.
- Include companion projects in `examples/<slug>/` with setup instructions, requirements, `.env.example` when applicable, tests, and VS Code launch configuration.
- Verify claims and link research sources. Distinguish reported research results from measurements taken in the example.
- Run relevant tests and commit articles and their companion code to Git. Never commit credentials.

## Medium mobile limitation

GitHub renders Markdown automatically, but **Medium's Android app does not reliably convert pasted Markdown into styled Medium headings and code blocks**. Markdown is now the preferred repository source format, not a guarantee of automatic mobile formatting in Medium. Use Medium's own formatting controls or a desktop Markdown-to-rich-text workflow and check the published draft.

## Legacy HTML

Existing `articles/reasoning-cache/index.html` and `articles/reasoning-cache/medium/index.html` are retained for old links only. Do not generate additional HTML article editions unless explicitly requested.

## Reference

[CPU-ARC](https://arxiv.org/abs/2611.09891) inspired the reasoning-cache article. The accompanying code is an independent and narrowly scoped educational implementation.
