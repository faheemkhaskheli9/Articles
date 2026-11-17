"""Opt-in model-assisted procedure synthesis; no arbitrary generated code execution."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import CURATED_STEPS, Checkout, reference_checkout, run_program, validate_steps


def generate_with_model(api_key: str, model: str) -> list[dict[str, str]]:
    """Request a constrained declarative procedure; independently verify it."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    order = Checkout(*map(__import__('decimal').Decimal, ('120', '10', '8', '5')))
    reference = reference_checkout(order)
    source = client.responses.create(
        model=model,
        input=(
            'Solve this checkout calculation and briefly describe the rules. '
            'Discount is applied before tax, tax excludes shipping, '
            'and every monetary step rounds to cents using ROUND_HALF_UP. '
            f'Input: subtotal={order.subtotal}, discount_pct={order.discount}, '
            f'tax_pct={order.tax}, shipping={order.shipping}. '
            'Give total and explanation.'
        ),
    )
    builder = client.responses.create(
        model=model,
        input=(
            'Create a JSON object with exactly one key "steps", containing exactly '
            'four objects in this precise order: discount_amount, taxable_subtotal, '
            'tax_amount, total. Each object has "name" and "expression". '
            'Expressions may use variables subtotal, discount, tax, shipping and '
            'previously declared step names; only arithmetic + - * / and numeric '
            'constants are supported. Percentages are numbers 0..100. '
            'Money amounts are rounded to two decimals after EACH step. '
            'Tax is calculated on discounted subtotal; shipping is not taxable. '
            'Return JSON only, no markdown. '
            f'Example result independently verified: {reference}. '
            f'Source model explanation: {source.output_text[:1800]}'
        ),
    )
    content = builder.output_text.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
    candidate: Any = json.loads(content)
    if not isinstance(candidate, dict) or set(candidate) != {'steps'}:
        raise ValueError('Unexpected builder output')
    steps = candidate['steps']
    validate_steps(steps)
    return steps


def save_generated(path: Path, steps: list[dict[str, str]], model: str) -> None:
    """Write approved declarative steps; no exec/eval of LLM output."""
    validate_steps(steps)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'version': 1, 'procedure': 'checkout-v1',
                               'origin': 'generated', 'model': model, 'steps': steps}, indent=2), encoding='utf-8')
