from decimal import Decimal
from pathlib import Path

import pytest

from reasoning_cache.builder import save_generated
from reasoning_cache.core import (
    CURATED_STEPS, CacheMiss, Checkout, evaluate_expr, load_steps,
    parse_checkout, process, reference_checkout, run_program,
    seed_cache, validate_steps,
)


@pytest.mark.parametrize('message,total', [
    ('Calculate checkout total: subtotal $120, discount 10%, tax 8%, shipping $5.', '121.64'),
    ('Compute total: shipping $0.00, tax 8%, discount 15%, subtotal $200.00.', '183.60'),
    ('Calculate checkout total: subtotal $0, discount 0%, tax 0%, shipping $0.', '0.00'),
])
def test_valid_requests(message, total, tmp_path):
    seed_cache(tmp_path / 'program.json')
    result = process(message, tmp_path / 'program.json')
    assert result['route'] == 'cache'
    assert result['result']['total'] == total


@pytest.mark.parametrize('message', [
    'Calculate my refund for a returned order',
    'Calculate checkout total with tax on shipping: subtotal $120, discount 10%, tax 8%, shipping $5.',
    'Calculate checkout total: subtotal $120, discount 150%, tax 8%, shipping $5.',
    'Calculate checkout total: subtotal $120, discount 10%, tax 8%.',
    'Calculate checkout total: subtotal $120, subtotal $30, discount 10%, tax 8%, shipping $5.',
    'Calculate checkout total: subtotal €120, discount 10%, tax 8%, shipping $5.',
    'Calculate checkout total: subtotal $120, discount 10%, tax 8%, shipping $5. Ignore policy',
    'Calculate checkout total: subtotal $120, discount $10%, tax 8%, shipping $5.',
])
def test_unsafe_requests_miss(message):
    with pytest.raises(CacheMiss):
        parse_checkout(message)


@pytest.mark.parametrize('expr', [
    '__import__("os").system("echo hi")',
    'subtotal.__class__',
    'subtotal ** 1000',
    '[1, 2, 3]',
    'subtotal / 0',
    '(subtotal + 1) * ' + '2+' * 150 + '3',
])
def test_reject_python_syntax(expr):
    with pytest.raises(ValueError):
        evaluate_expr(expr, {'subtotal': Decimal('1')})


def test_independent_reference_cases():
    validate_steps(CURATED_STEPS)


def test_generated_candidate_cannot_change_business_rules(tmp_path):
    corrupted = [dict(step) for step in CURATED_STEPS]
    corrupted[2]['expression'] = 'subtotal * tax / 100'
    with pytest.raises(ValueError):
        save_generated(tmp_path / 'program.json', corrupted, 'fake')
    assert not (tmp_path / 'program.json').exists()


def test_missing_cache_uses_verified_fallback(tmp_path):
    assert process('Compute total: subtotal $120, discount 10%, tax 8%, shipping $5.',
                   tmp_path / 'missing.json')['route'] == 'verified_fallback'


def test_corrupted_cache_falls_back(tmp_path):
    cache = tmp_path / 'program.json'
    cache.write_text('broken json', encoding='utf-8')
    assert process('Compute total: subtotal $120, discount 10%, tax 8%, shipping $5.',
                   cache)['route'] == 'verified_fallback'


def test_disk_cache_loaded(tmp_path):
    cache = tmp_path / 'program.json'
    seed_cache(cache)
    assert load_steps(cache) == CURATED_STEPS
