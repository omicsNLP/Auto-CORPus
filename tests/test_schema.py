"""Tests for the table JSON schema file."""

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft4Validator


@pytest.fixture
def table_schema() -> dict[str, Any]:
    """The parsed contents of the table schema JSON file."""
    schema_path = Path(__file__).parent.parent / "keyFiles" / "table_schema.json"
    with schema_path.open(encoding="utf-8") as f:
        return json.load(f)


def test_table_schema_valid(table_schema):
    """Test whether the table JSON schema is valid."""
    Draft4Validator.check_schema(table_schema)


def test_table_output_files_valid(table_schema, data_path: Path):
    """Test whether table output JSON files in data folder are valid."""
    files = [path for path in data_path.rglob("*_tables.json") if path.is_file()]
    assert files

    validator = Draft4Validator(table_schema)
    for file in files:
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
        assert validator.is_valid(data)
