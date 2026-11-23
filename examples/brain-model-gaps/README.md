# Brain-model gaps: same wiring, different dynamics

A **synthetic** three-node recurrent tanh network demonstrates that identical directed connectivity and edge signs can produce different activity when strengths differ. The same constant sensory input yields different motor output.

This is not a biological neural simulation, brain emulation, or neuroscience benchmark. The values are illustrative rather than measurements of living tissue.

## Setup

Python 3.11+; no GPU or API key.

    cd examples/brain-model-gaps
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python -m brain_gap_lab --json
    python -m unittest discover -s tests -v

On Windows use .venv\Scripts\activate.

From repository root, validate Medium HTML:

    python tools/build_medium_html.py brain-model-gaps --check

Modify connection strengths in src/brain_gap_lab/__init__.py, then rerun tests. The example has no learning, spiking neurons, glia, biochemistry, body, or biological data. To test neuroscience hypotheses, use measured circuits with held-out intervention outcomes and quantified uncertainty.

[Main article](../../articles/brain-model-gaps/article.md).
