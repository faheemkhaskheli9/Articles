# Adversarial review — Reward is not success

**Reviewed:** 2026-11-18. **Artifact:** `articles/reward-is-not-success/article.md` and `examples/reward-is-not-success/`.

## Verdict

**Publish with qualifications.** The Brain research numbers and primary statistical conclusion are consistent with the [frozen research report](https://github.com/faheemkhaskheli9/Brain/blob/main/research/continuous-motor-results-2026-11-12.md), but the original article title implied that the target-contact decline was demonstrated. It was **not statistically conclusive**. The toy example also has a deliberately constructed reward/termination interaction that needs to be explicit. Both issues were corrected.

## Red-team findings, corrections and evidence

1. **High — Inference too strong in title/hook.** Observed contact was 22.66% versus 25.29%, but the paired difference was −2.64 percentage points with 95% CI [−7.37,+1.83] and p=0.3125. A sample point estimate must not be presented as a demonstrated deterioration. **Fix:** question-form title and repeated distinction between descriptive decline and lack of evidence for a true reduction.
2. **High — Educational example has a strong scoring artifact.** Early goal contact stops movement; unused slots count as zero reward, so a fast successful policy loses opportunities for +1 progress. The cautious policy is structurally incapable of reaching the goal within 16 actions. This proves a score/goal mismatch is possible, **not** that real agents learn to exploit it or that the published Brain experiment uses the same reward mechanism. **Fix:** explicit explanation in article and example README.
3. **High — Cherry-picked toy conditions.** The default settings heavily favor bold on goal completion. Local sensitivity analysis (200 deterministic paired episodes/condition, seed 42) gave goal rates: 16 steps/30% slips (0%,88.5%), 32 steps/30% (97%,100%), 40 steps/70% (78.5%,12.5%) for cautious/bold. **Fix:** add `--stress-test` and a regression test demonstrating that the goal ranking can reverse. These scenarios are exploratory.
4. **Medium — Missing input validation.** NaN and infinity goals slipped past `goal <= 0`, allowing meaningless outputs. **Fix:** require finite goal and slip parameters in configuration and single-episode calls; add boundary tests.
5. **Medium — Medium HTML contains an unresolved nested placeholder.** The previous generated HTML contained a literal NUL-delimited token in the `reward_gap.py` link label instead of the expected code-styled text, due to the earlier conversion process. **Fix:** regenerate HTML with proper recursive token resolution, and verify absence of NUL placeholders, empty list items and blank pre blocks. This static check **does not** prove that Medium's importer preserves the layout.
6. **Medium — Research scope is narrow.** Only ten reserved simulated seeds, two pretrained checkpoints, engineered reward and single-joint motor dynamics. The frozen protocol commit is [4fe342e](https://github.com/faheemkhaskheli9/Brain/commit/4fe342e487eb9da213e2482e158fa3ae8c332be2). The agent did **not** train a new skill online. **Fix:** retain and foreground those limitations; do not claim human neuroscience or AGI implications.
7. **Low — Weak exact-output regression.** The prior suite checked only qualitative ranking differences. **Fix:** check seed-42 default metrics exactly (within floating tolerances) and add a context where the winner reverses.

## Verification performed

- Retrieved the GitHub article, companion code, tests and Brain research report.
- Verified that the reward paper is [Karwowski et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6ad68a54eaa8f9bf6ac698b02ec05048-Abstract-Conference.html); the [DeepMind specification-gaming post](https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/) exists and supports the conceptual comparison.
- Reconstructed the source-controlled Python script and tests in a local scratch directory, ran the original tests (**13/13 passed**) and reproduced the article's fixed-seed output. Added input and stress-case tests and ran the revised suite (**20/20 passed**) and `python -m py_compile`.
- The corrected HTML was generated from the revised Markdown with the repository's converter semantics; static markup checks were applied.
- No published Medium import was executed, and the live GitHub Pages URL could not be confirmed through the available web fetcher. **Do not mark mobile or Medium formatting as end-to-end validated.**

## Remaining limitations and falsifiers

- Add multiple independent seeds, varied target positions and explicit confidence intervals to a future scientific benchmark. A deterministic educational example is not an independent experiment.
- Benchmark goal completion as a precommitted primary endpoint, with time/energy/action costs and risk constraints reported separately.
- Test unrehearsed motor regimes lacking a matching saved checkpoint, rather than only A/B policy selection.
- Use raw observations and realistic delayed/noisy feedback before arguing that the method generalizes to embodied intelligence.
- Independently validate the actual Medium import result in the Medium editor on mobile, especially code blocks and list semantics.
