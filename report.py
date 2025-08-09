import json

class LogProcessor:
    def __init__(self, files: list) -> None:
        self.files = files
        self.lines: list[dict] = []
        self.fields: set[str] = set()

        for path in files:
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
                    self.lines.append(obj)
                    self.fields.update(obj.keys())

        print(f'Loaded {len(self.lines)} lines')
        print(f'Found fields: {sorted(self.fields)}')

    def _get_values(self, field: str):
        field_values = [entry.get(field) for entry in self.lines if entry.get(field) is not None]
        return field_values

    def _get_count(self, field: str):
        field_values = self._get_values(field)
        count = {}

        for value in field_values:
            count[value] = count.get(value, 0) + 1

        return count

    def _get_average(self, field: str, target: str = 'request_method'):
        totals = {}
        counts = {}

        for entry in self.lines:
            field_value = entry.get(field)
            target_value = entry.get(target)

            if field_value is not None and isinstance(target_value, (int, float)):
                totals[field_value] = totals.get(field_value, 0) + target_value
                counts[field_value] = counts.get(field_value, 0) + 1

        averages = {key: totals[key] / counts[key] for key in totals}
        return averages



if __name__ == '__main__':
    files = [
        'exm/example1.log',
        'exm/example2.log'
    ]

    processor = LogProcessor(files)

    fields = [
        #'@timestamp',
        #'status',
        'url',
        #'request_method',
        #'response_time',
        #'http_user_agent',
    ]

    for field in fields:
        report = processor._get_average(field)
