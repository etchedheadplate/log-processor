import json

class LogProcessor:
    def __init__(self, path: str) -> None:
        self.entries = []

        with open(path, 'r', encoding='utf-8') as log:
            for num, line in enumerate(log, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Line {num} in {path} is not valid JSON: {exc}"
                    ) from exc
                self.entries.append(obj)

        print(f"Loaded {len(self.entries)} entries")
        print(json.dumps(self.entries, indent = 4))
