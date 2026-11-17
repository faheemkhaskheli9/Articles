# Verified Mistake Memory: runnable companion

Independent, offline educational example for the article [Your AI Agent Didn't Learn. It Just Remembered](../../articles/your-ai-agent-didnt-learn-it-just-remembered/article.md), based on patterns researched in the [Brain project](https://github.com/faheemkhaskheli9/Brain/blob/main/research/llm-mistake-learning.md).

It demonstrates a feedback gate, isolated lexical retrieval, local persistence, training/evaluation separation, and an optional OpenAI model adapter. **Offline model and oracle are deterministic synthetic functions, not an LLM benchmark.** The memory updates inference context, not model parameters.

## Run offline (Python 3.11+)

```bash
git clone https://github.com/faheemkhaskheli9/Articles.git
cd Articles/examples/verified-mistake-memory
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -r requirements.txt
python memory_agent.py
python -m pytest -q
```

Expected output: the deliberately broken toy model solves **0/2** previously unseen synthetic word-pair tasks with memory off and **2/2** with memory on, after one independently verified training correction. These are deterministic fixture counts, not evidence that any actual LLM improves.

## Optional live model (paid API)

```bash
python -m pip install -r requirements-llm.txt
cp .env.example .env  # Windows: copy .env.example .env
# Set OPENAI_API_KEY and choose an available OPENAI_MODEL in .env.
python openai_demo.py
```

The live adapter uses OpenAI's Responses API to answer a single synthetic task. The built-in oracle verifies only that one task family. Real-model output may succeed immediately or fail; this is **not** a validated comparative evaluation. Credentials are read locally and are not recorded by the demo. The optional adapter is not exercised in the offline tests and needs a valid paid API key.

VS Code: open this directory, select the virtual environment, and use `.vscode/launch.json` for the demo or tests.

## Safety and research limitations

- A caller-supplied verifier is the trust boundary. If it is compromised or incorrect, a bad correction can still pass.
- Lexical retrieval is deliberately weak. A matching lesson does not prove applicability, and the toy model follows any retrieved lesson.
- `scope` is an application-provided label, **not authentication** or production-grade multi-tenant isolation. The JSON store is not encrypted. Do not store private information.
- The parser is restricted to artificial `Last word:` tasks. The code does not perform real operations or train a model.
- Held-out leakage checking catches exact prompt matches, not semantic duplicates. The 2-case demo is too small to estimate generalization.
- Production systems need trusted verifiers, access controls, provenance review, conflict resolution, retention/deletion, adversarial tests, and matched-budget evaluation.
