import argparse
import json
from pathlib import Path

from .pipeline import build_pipeline
from .simu5g_pipeline import build_simu5g_pipeline


def _validate_source_input(
    parser: argparse.ArgumentParser,
    source: str,
    input_path: Path,
) -> None:
    if not input_path.exists():
        parser.error(f"--input does not exist: {input_path}")

    if source == "simu5g":
        if not input_path.is_file():
            parser.error(
                f'For --source=simu5g, --input must be a CSV file, not "{input_path}".'
            )
        if input_path.suffix.lower() != ".csv":
            parser.error(
                f'For --source=simu5g, --input must point to a .csv file, got "{input_path.name}".'
            )
        return

    if source == "van3twin_ns3":
        if input_path.is_dir():
            return
        if input_path.is_file() and input_path.suffix.lower() == ".csv":
            return
        parser.error(
            "For --source=van3twin_ns3, --input must be either "
            "an artifacts directory or a .csv file."
        )
        return

    parser.error(f"Unsupported source: {source}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="NEWWAY unified results pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build",
        help="Build normalized results from supported sources",
    )
    build_parser.add_argument(
        "--source",
        choices=["van3twin_ns3", "simu5g"],
        required=True,
        help=(
            "Source stack. "
            "van3twin_ns3 accepts an artifacts directory or a single CSV file; "
            "simu5g accepts a single opp_scavetool-exported CSV file."
        ),
    )
    build_parser.add_argument(
        "--input",
        required=True,
        help="Input path for the selected source.",
    )
    build_parser.add_argument(
        "--output",
        required=True,
        help="Output directory for generated artifacts.",
    )
    build_parser.add_argument(
        "--scenario",
        required=True,
        help="Scenario name.",
    )
    build_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional explicit run id.",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "build":
        parser.error(f"Unsupported command: {args.command}")

    input_path = Path(args.input)
    output_path = Path(args.output)

    _validate_source_input(parser, args.source, input_path)
    output_path.mkdir(parents=True, exist_ok=True)

    if args.source == "simu5g":
        result = build_simu5g_pipeline(
            input_csv=str(input_path),
            output_dir=str(output_path),
            scenario=args.scenario,
            run_id=args.run_id,
        )
    else:
        result = build_pipeline(
            input_dir=str(input_path),
            output_dir=str(output_path),
            scenario=args.scenario,
            run_id=args.run_id,
        )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()