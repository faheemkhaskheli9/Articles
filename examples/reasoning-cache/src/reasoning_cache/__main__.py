"""Run python -m reasoning_cache from the example directory after installation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .builder import generate_with_model, save_generated
from .core import CacheMiss, parse_checkout, process, seed_cache


def main() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description='Validated checkout reasoning cache demo')
    parser.add_argument('--request', default='Calculate checkout total: subtotal $120, discount 10%, tax 8%, shipping $5.')
    parser.add_argument('--cache-path', type=Path, default=Path('.cache/procedures.json'))
    parser.add_argument('--seed', action='store_true', help='Install tested curated procedure (offline)')
    parser.add_argument('--build', action='store_true', help='Synthesize and validate a procedure using OpenAI (paid API)')
    args = parser.parse_args()

    try:
        if args.seed and args.build:
            parser.error('--seed and --build are mutually exclusive')
        if args.seed:
            seed_cache(args.cache_path)
            print('Seeded validated procedure at', args.cache_path)
        if args.build:
            parse_checkout(args.request)
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                parser.error('--build requires OPENAI_API_KEY in .env or environment')
            model = os.environ.get('OPENAI_MODEL', 'gpt-4.1-mini')
            steps = generate_with_model(api_key, model)
            save_generated(args.cache_path, steps, model)
            print('Model-synthesized procedure validated and saved at', args.cache_path)
        print(json.dumps(process(args.request, args.cache_path), indent=2))
        return 0
    except (CacheMiss, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(status=2, message=f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
