import argparse
import sys

from report import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate reports from JSON-structured log files.")
    parser.add_argument(
        "--file", "-f", nargs="+", required=True, help="Log file(s) to process (one or more files)"
    )
    parser.add_argument(
        "--report",
        "-r",
        choices=["average", "median"],
        default="average",
        help="Report type to generate (default: average)",
    )
    parser.add_argument("--field", "-F", default="url", help="Field to group by (default: url)")
    parser.add_argument(
        "--target",
        "-t",
        default="response_time",
        help="Target field to analyze (default: response_time)",
    )
    parser.add_argument(
        "--date", "-d", default=None, help="Filter logs by date (YYYY-MM-DD), optional"
    )

    args = parser.parse_args()

    try:
        processor = ReportGenerator(
            files=args.file, field=args.field, target=args.target, date=args.date
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    report_name = f"report_{args.report}"
    if not hasattr(processor, report_name):
        print(f'Error: Report "{report_name}" does not exist.', file=sys.stderr)
        sys.exit(1)

    report = getattr(processor, report_name)
    report()


if __name__ == "__main__":
    main()
