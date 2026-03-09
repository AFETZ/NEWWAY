import argparse
from pprint import pprint

from .pipeline import build_pipeline


def main():
    parser = argparse.ArgumentParser(description="NEWWAY results pipeline MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build normalized results from CSV artifacts")
    build_parser.add_argument("--input", required=True, help="Input artifacts directory")
    build_parser.add_argument("--output", required=True, help="Output directory")
    build_parser.add_argument("--scenario", required=True, help="Scenario name")
    build_parser.add_argument("--run-id", default=None, help="Optional explicit run id")

    args = parser.parse_args()

    if args.command == "build":
        result = build_pipeline(
            input_dir=args.input,
            output_dir=args.output,
            scenario=args.scenario,
            run_id=args.run_id,
        )
        pprint(result)


if __name__ == "__main__":
    main()
