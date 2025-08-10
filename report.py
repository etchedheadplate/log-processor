import os
import json
from tabulate import tabulate
from datetime import datetime
from statistics import median
from typing import Optional, Dict

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
            raise FileNotFoundError(f'the following file(s) do not exist: {", ".join(missing_files)}')

        if date:
            try:
                self.date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError as exc:
                raise ValueError(f'date "{date}" is not a valid date (expected YYYY-MM-DD)') from exc

        for file in self.files:
            self._parse_file(file)

        self._filter_fields()

        if self.field not in self.fields:
            valid_fields = '\n    '.join(sorted([f for f in self.fields if f != '_parsed_timestamp']))
            raise ValueError(f"'{self.field}' is not valid field, expected:\n    {valid_fields}")
        if self.target not in self.fields:
            valid_targets = '\n    '.join(sorted([f for f in self.fields if f not in ['_parsed_timestamp', self.field]]))
            raise ValueError(f"'{self.target}' is not valid target, expected:\n    {valid_targets}")
        if self.field == self.target:
            raise ValueError("field and target can't be the same")

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
                        f'line {num} in {file} is not valid JSON: {exc}'
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

    def _filter_fields(self) -> None:
        usable_fields = set()
        for field in self.fields:
            is_usable = True
            for entry in self.lines:
                val = self._get_nested_value(entry, field)
                if isinstance(val, dict):
                    is_usable = False
                    break
            if is_usable:
                usable_fields.add(field)
        self.fields = usable_fields

    def _get_nested_value(self, data: dict, path: str):
        keys = path.split('/')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def _group_target_values(self):
        grouped_values = {}
        for entry in self.lines:
            field_value = self._get_nested_value(entry, self.field)
            target_value = self._get_nested_value(entry, self.target)

            if field_value is not None and isinstance(target_value, (int, float)):
                grouped_values.setdefault(field_value, []).append(target_value)

        counts: Dict = {key: len(vals) for key, vals in grouped_values.items()}
        return grouped_values, counts

    def _print_report(self, table_data: list, headers: list) -> None:
        print(tabulate(table_data, headers=headers))

    def report_average(self) -> None:
        grouped_values, counts = self._group_target_values()
        if not grouped_values:
            print(f'No valid data found for field "{self.field}" and target "{self.target}"')
            return

        averages = {key: sum(vals) / len(vals) for key, vals in grouped_values.items()}
        sorted_items = sorted(averages.items(), key=lambda kv: counts[kv[0]], reverse=True)

        table_data = []
        for index, (value, avg) in enumerate(sorted_items, start=1):
            total = counts[value]
            table_data.append([index, value, total, round(avg, 3)])

        headers = ['', self.field, 'total', f'avg_{self.target}']
        self._print_report(table_data, headers)

    def report_median(self) -> None:
        grouped_values, counts = self._group_target_values()
        if not grouped_values:
            print(f'No valid data found for field "{self.field}" and target "{self.target}"')
            return

        medians = {key: median(vals) for key, vals in grouped_values.items()}
        sorted_items = sorted(medians.items(), key=lambda kv: counts[kv[0]], reverse=True)

        table_data = []
        for index, (value, med) in enumerate(sorted_items, start=1):
            total = counts[value]
            table_data.append([index, value, total, round(med, 3)])

        headers = ['', self.field, 'total', f'med_{self.target}']
        self._print_report(table_data, headers)
