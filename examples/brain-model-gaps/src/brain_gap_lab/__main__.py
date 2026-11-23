"""Entry point for the educational circuit experiment."""
import argparse
import json
from . import comparison


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = comparison(args.steps)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print("Synthetic example, not biological evidence")
        for key, value in data.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
