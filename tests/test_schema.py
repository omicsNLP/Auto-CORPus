"""Tests for the table JSON schema file."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft4Validator

_TESTS_PATH = Path(__file__).parent
_REPO_PATH = _TESTS_PATH.parent
_SCHEMA_PATH = _REPO_PATH / "keyFiles" / "table_schema.json"


@pytest.fixture
def table_schema():
    """The parsed contents of the table schema JSON file."""
    with _SCHEMA_PATH.open() as f:
        return json.load(f)


def test_table_schema_valid(table_schema):
    """Test whether the table JSON schema is valid."""
    Draft4Validator.check_schema(table_schema)


def test_table_output_files_valid(table_schema):
    """Test whether table output JSON files in data folder are valid."""
    files = [
        path for path in (_TESTS_PATH / "data").rglob("*_tables.json") if path.is_file()
    ]
    assert files

    validator = Draft4Validator(table_schema)
    for file in files:
        with open(file) as f:
            data = json.load(f)
        assert validator.is_valid(data)
