# Article authoring rules

- **Markdown only:** Create new articles and update substantive article content as GitHub-flavored Markdown at `articles/<slug>/article.md`. Do not generate new HTML article pages or Medium-specific HTML editions unless explicitly requested.
- Markdown is the canonical source for the article. Retain legacy HTML URLs for compatibility, but do not use those files as editable article sources.
- Each AI article should focus on practical coding: the problem, use cases, a worked scenario, step-by-step implementation, runnable examples, tests, adversarial cases, expert considerations, and credible citations.
- Maintain a companion project under `examples/<slug>/` including dependencies, `.env.example` where relevant, VS Code launch configuration, README, and tests.
- Check examples against real repository behavior, run relevant tests, and keep Git history clear. Do not invent benchmark figures or test results.
- GitHub renders Markdown; Medium mobile may not. Never imply a pasted Markdown article automatically becomes formatted on Medium Android.
