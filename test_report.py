import json
import pytest
from datetime import datetime
from report import ReportGenerator


LOG_ENTRIES = [
    json.dumps({
        "@timestamp": "2025-08-10T12:00:00Z",
        "url": "/api/endpoint1/...",
        "response_time": 120,
        "http_user_agent": {
            "os": {
                "name": "Windows"
            }
        }
    }),
    json.dumps({
        "@timestamp": "2025-08-10T12:05:00Z",
        "url": "/api/endpoint2/...",
        "response_time": 150,
        "http_user_agent": {
            "os": {
                "name": "Linux"
            }
        }
    }),
    json.dumps({
        "@timestamp": "2025-08-09T10:00:00Z",
        "url": "/api/endpoint1/...",
        "response_time": 100
    }),
    json.dumps({
        "@timestamp": "2025-08-10T12:10:00Z",
        "url": "/api/endpoint1/...",
        "response_time": 130
    }),
]

@pytest.fixture
def log_file(tmp_path):
    file_path = tmp_path / "temp.log"
    file_path.write_text("\n".join(LOG_ENTRIES))
    return str(file_path)


def test_init_valid_fields_and_targets(log_file):
    rg = ReportGenerator(files=[log_file], field="url", target="response_time")
    assert rg.field == "url"
    assert rg.target == "response_time"
    assert isinstance(rg.lines, list)
    assert len(rg.lines) > 0
    assert "url" in rg.fields
    assert "response_time" in rg.fields


def test_init_no_files():
    with pytest.raises(FileNotFoundError, match="provide path to a log file"):
        ReportGenerator(files=[])


def test_init_invalid_file():
    with pytest.raises(FileNotFoundError, match=r"the following file"):
        ReportGenerator(files=["nonexistent.log"])


def test_init_invalid_field(log_file):
    with pytest.raises(ValueError, match="is not valid field"):
        ReportGenerator(files=[log_file], field="nonexistent_field", target="response_time")


def test_init_invalid_target(log_file):
    with pytest.raises(ValueError, match="is not valid target"):
        ReportGenerator(files=[log_file], field="url", target="nonexistent_target")


def test_init_field_target_same(log_file):
    with pytest.raises(ValueError, match="field and target can't be the same"):
        ReportGenerator(files=[log_file], field="url", target="url")


def test_init_invalid_date_format(log_file):
    with pytest.raises(ValueError, match="not a valid date"):
        ReportGenerator(files=[log_file], date="not_a_date")


def test_date_filtering(log_file):
    rg = ReportGenerator(files=[log_file], date="2025-08-10")
    assert all(
        line.get('_parsed_timestamp') and
        line['_parsed_timestamp'].date() == datetime.strptime("2025-08-10", "%Y-%m-%d").date()
        for line in rg.lines
    )


def test_group_target_values(log_file):
    rg = ReportGenerator(files=[log_file])
    grouped, counts = rg._group_target_values()

    assert isinstance(grouped, dict)
    assert all(isinstance(vals, list) for vals in grouped.values())
    assert all(isinstance(c, int) for c in counts.values())

    assert "/api/endpoint1/..." in grouped
    assert "/api/endpoint2/..." in grouped


def test_report_average_output(log_file, capsys):
    rg = ReportGenerator(files=[log_file])
    rg.report_average()

    captured = capsys.readouterr().out
    assert "avg_response_time" in captured
    assert "/api/endpoint1/..." in captured
    assert "/api/endpoint2/..." in captured


def test_report_median_output(log_file, capsys):
    rg = ReportGenerator(files=[log_file])
    rg.report_median()

    captured = capsys.readouterr().out
    assert "med_response_time" in captured
    assert "/api/endpoint1/..." in captured
    assert "/api/endpoint2/..." in captured


def test_flatten_keys_simple(log_file):
    rg = ReportGenerator(files=[log_file])
    nested_dict = {
        "a": {
            "b": 1,
            "c": {
                "d": 2
            }
        },
        "e": 3
    }
    keys = rg._flatten_keys(nested_dict)
    expected_keys = ['a', 'a/b', 'a/c', 'a/c/d', 'e']
    assert set(keys) == set(expected_keys)


def test_get_nested_value(log_file):
    rg = ReportGenerator(files=[log_file])
    data = {
        "a": {
            "b": {
                "c": 123
            }
        }
    }
    val = rg._get_nested_value(data, "a/b/c")
    assert val == 123
    val = rg._get_nested_value(data, "a/b/x")
    assert val is None
    val = rg._get_nested_value(data, "a")
    assert isinstance(val, dict)


def test_filter_fields_removes_dict_values(log_file):
    entries = [
        {"a": 1, "b": {"c": 2}},
        {"a": 3, "b": {"d": 4}},
    ]
    rg = ReportGenerator(files=[log_file])
    rg.lines = entries
    rg.fields = {"a", "b"}
    rg._filter_fields()
    assert "a" in rg.fields
    assert "b" not in rg.fields


BAD_LOG_ENTRY = [
    json.dumps({
        "not_a_@timestamp": "2025-08-10T12:00:00Z",
        "url": 111,
        "response_time": "not_a_number",
        222: {
            "subdict": ["not", "a", "dict"]
        }
    }),
]

@pytest.fixture
def bad_log_file(tmp_path):
    file_path = tmp_path / "bad.log"
    file_path.write_text("\n".join(BAD_LOG_ENTRY))
    return str(file_path)


def test_unexpected_structure_in_log(bad_log_file, capsys):
    rg = ReportGenerator(files=[bad_log_file], field="url", target="response_time")

    assert rg.lines[0]['_parsed_timestamp'] is None

    assert "url" in rg.fields
    assert isinstance(rg._get_nested_value(rg.lines[0], "url"), int)

    grouped, counts = rg._group_target_values()
    assert grouped == {}
    assert counts == {}

    flat_keys = rg._flatten_keys(rg.lines[0])
    assert any(key.startswith("222/") for key in flat_keys)

    rg.report_average()
    captured_average = capsys.readouterr().out
    assert "No valid data found for field" in captured_average
