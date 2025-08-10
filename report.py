import os
import json
from tabulate import tabulate
from datetime import datetime
from typing import Optional

class ReportGenerator:
    def __init__(
        self,
        files: list,
        field: str = 'url',
        target: str = 'response_time',
        date: Optional[str] = None
    ) -> None:
        self.files = files
        self.field = field
        self.target = target
        self.date = None
        self.lines: list[dict] = []
        self.fields: set[str] = set()

        missing_files = [file for file in self.files if not os.path.exists(file)]
        if missing_files:
            raise FileNotFoundError(f'The following file(s) do not exist: {", ".join(missing_files)}')

        if date:
            try:
                self.date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError as exc:
                raise ValueError(f'date "{date}" is not a valid date (expected YYYY-MM-DD)') from exc

        for file in self.files:
            self._parse_file(file)

        if self.field not in self.fields:
            raise ValueError(f'"{self.field}" is not present in logs (present: {self.fields})')
        if self.target not in self.fields:
            raise ValueError(f'"{self.target}" is not present in logs (present: {self.fields})')

    def _flatten_keys(self, data: dict, parent_key: str = '') -> list[str]:
        keys = []
        for key, value in data.items():
            new_key = f'{parent_key}/{key}' if parent_key else key
            keys.append(new_key)
            if isinstance(value, dict):
                keys.extend(self._flatten_keys(value, new_key))
        return keys

    def _parse_file(self, file: str) -> None:
        with open(file, 'r', encoding='utf-8') as log:
            for num, line in enumerate(log, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f'Line {num} in {file} is not valid JSON: {exc}'
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

                if self.date:
                    ts_date = obj['_parsed_timestamp'].date() if obj['_parsed_timestamp'] else None
                    if ts_date != self.date:
                        continue

                self.lines.append(obj)
                self.fields.update(self._flatten_keys(obj))

    def _get_nested_value(self, data: dict, path: str):
        keys = path.split('/')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None  # Path does not exist
        return value

    def _print_report(self, table_data: list, headers: list) -> None:
        print(tabulate(table_data, headers=headers))

    def report_average(self) -> None:
        totals = {}
        counts = {}

        for entry in self.lines:
            field_value = self._get_nested_value(entry, self.field)
            target_value = self._get_nested_value(entry, self.target)

            if field_value is not None and isinstance(target_value, (int, float)):
                totals[field_value] = totals.get(field_value, 0) + target_value
                counts[field_value] = counts.get(field_value, 0) + 1

        if not totals:
            print(f'No valid data found for field "{self.field}" and target "{self.target}"')
            return

        averages = {key: totals[key] / counts[key] for key in totals}

        sorted_items = sorted(averages.items(), key=lambda kv: counts[kv[0]], reverse=True)

        table_data = []
        for index, (value, avg) in enumerate(sorted_items, start=1):
            total = counts[value]
            table_data.append([index, value, total, round(avg, 3)])

        headers = ['', self.field, 'total', f'avg_{self.target}']

        self._print_report(table_data, headers)




if __name__ == '__main__':
    files = [
        #'exm/example1.log',
        #'exm/example2.log',
        'exm/example_ext.log'
    ]

    date = '2025-06-22'

    field = 'url'

    target = 'bytes_sent'

    fields = [
        #'@timestamp',
        #'status',
        'url',
        #'request_method',
        #'response_time',
        #'http_user_agent',
    ]

    processor = ReportGenerator(files=files, field=field, target=target)
    processor.report_average()

'''
    for field in fields:
        processor = ReportGenerator(files=files, field=field, date=date)
        processor.report_average()
'''
