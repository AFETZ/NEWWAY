import argparse
import json
from pprint import pprint

from .pipeline import build_pipeline
from .simu5g_pipeline import build_simu5g_pipeline


def main():
    parser = argparse.ArgumentParser(description="NEWWAY unified results pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build normalized results from supported sources")
    build_parser.add_argument("--source", choices=["van3twin_ns3", "simu5g"], default="van3twin_ns3", help="Source stack")
    build_parser.add_argument("--input", required=True, help="Input path: artifacts directory for van3twin_ns3, CSV file for simu5g")
    build_parser.add_argument("--output", required=True, help="Output directory")
    build_parser.add_argument("--scenario", required=True, help="Scenario name")
    build_parser.add_argument("--run-id", default=None, help="Optional explicit run id")

    args = parser.parse_args()

    if args.command == "build":
        if args.source == "simu5g":
            result = build_simu5g_pipeline(
                input_csv=args.input,
                output_dir=args.output,
                scenario=args.scenario,
                run_id=args.run_id,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        result = build_pipeline(
            input_dir=args.input,
            output_dir=args.output,
            scenario=args.scenario,
            run_id=args.run_id,
        )
        pprint(result)


if __name__ == "__main__":
    main()
