# Installation

```bash
git clone https://github.com/etchedheadplate/log-report.git
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Usage
```bash
python3 main.py --file FILE [FILE ...] [--report {average,median}] [--field FIELD] [--target TARGET] [--date DATE]
```

# Examples

**Default:** Generate average `{response_time}` reports grouped by unique `{url}` entries from JSON log files:

```bash
python3 main.py --file exm/example1.log exm/example2.log --report average
```

**Complex:** Generate median `{bytes_sent}` reports grouped by `{http_user_agent}/{os}/{name}` for a specific date:

```bash
python3 main.py --file exm/example_ext.log --report median --field http_user_agent/os/name --target bytes_sent --date 2025-06-23
```

# Extending Reports

To add new report types, implement a new method in `ReportGenerator` prefixed with `report_` that calls `self._print_report(table_data, headers)` with appropriate data formatted for the `tabulate` library.
