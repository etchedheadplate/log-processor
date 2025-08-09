import json
from tabulate import tabulate
from datetime import datetime
from typing import Optional

class ReportGenerator:
    def __init__(self, files: list, report: str = 'average', field: str = 'url', filter_date: Optional[str] = None) -> None:
        self.files = files
        self.lines: list[dict] = []
        self.fields: set[str] = set()
        self.filter_date = None
        self.reports = {
            'average': self._report_average,
            #'median': self._report_median,
            }

        if filter_date:
            try:
                self.filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            except ValueError as exc:
                raise ValueError(f'filter_date "{filter_date}" is not a valid date (expected YYYY-MM-DD)') from exc

        self._parse_files()

    def _parse_files(self) -> None:
        for path in self.files:
            with open(path, 'r', encoding='utf-8') as log:
                for num, line in enumerate(log, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            f'Line {num} in {path} is not valid JSON: {exc}'
                        ) from exc

                    timestamp_str = obj.get('@timestamp')
                    if timestamp_str:
                        try:
                            parsed_ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            obj['_parsed_timestamp'] = parsed_ts
                        except ValueError:
                            obj['_parsed_timestamp'] = None
                    else:
                        obj['_parsed_timestamp'] = None

                    if self.filter_date:
                        ts_date = obj['_parsed_timestamp'].date() if obj['_parsed_timestamp'] else None
                        if ts_date != self.filter_date:
                            continue

                    self.lines.append(obj)
                    self.fields.update(obj.keys())

    def _get_values(self, field: str) -> list:
        field_values = [entry.get(field) for entry in self.lines if entry.get(field) is not None]
        return field_values

    def _report_average(self, field: str, target: str = 'response_time') -> None:
        totals = {}
        counts = {}

        for entry in self.lines:
            field_value = entry.get(field)
            target_value = entry.get(target)

            if field_value is not None and isinstance(target_value, (int, float)):
                totals[field_value] = totals.get(field_value, 0) + target_value
                counts[field_value] = counts.get(field_value, 0) + 1

        averages = {key: totals[key] / counts[key] for key in totals}

        sorted_items = sorted(averages.items(), key=lambda kv: counts[kv[0]], reverse=True)

        table_data = []
        for index, (value, avg) in enumerate(sorted_items, start=1):
            total = counts[value]
            table_data.append([index, value, total, round(avg, 3)])

        headers = ['', field, 'total', f'avg_{target}']

        self._print_report(table_data, headers)

    def _print_report(self, table_data: list, headers: list, filter_date=None):
        print(tabulate(table_data, headers=headers))



if __name__ == '__main__':
    files = [
        'exm/example1.log',
        'exm/example2.log'
    ]

    filter_date = '2025-06-22'

    processor = ReportGenerator(files, filter_date=filter_date)

    fields = [
        #'@timestamp',
        #'status',
        'url',
        #'request_method',
        #'response_time',
        #'http_user_agent',
    ]

    for field in fields:
        processor._report_average(field)
