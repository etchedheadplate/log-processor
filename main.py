import argparse
import sys
from report import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description='Generate reports from log files.')
    parser.add_argument(
        '--file', '-f', nargs='+', required=True,
        help='Log file(s) to process (one or more files)'
    )
    parser.add_argument(
        '--report', '-r', choices=['average', 'median'], default='average',
        help='Report type to generate (default: average)'
    )
    parser.add_argument(
        '--field', '-F', default='url',
        help='Field to group by (default: url)'
    )
    parser.add_argument(
        '--target', '-t', default='response_time',
        help='Target field to analyze (default: response_time)'
    )
    parser.add_argument(
        '--date', '-d', default=None,
        help='Filter logs by date (YYYY-MM-DD), optional'
    )

    args = parser.parse_args()

    try:
        # Create instance with parsed args
        report_gen = ReportGenerator(
            files=args.file,
            field=args.field,
            target=args.target,
            date=args.date
        )
    except (FileNotFoundError, ValueError) as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

    # Compose method name and check if it exists
    method_name = f'report_{args.report}'
    if not hasattr(report_gen, method_name):
        print(f'Error: Report method "{method_name}" does not exist.', file=sys.stderr)
        sys.exit(1)

    # Call the method dynamically
    method = getattr(report_gen, method_name)
    method()

if __name__ == '__main__':
    main()
