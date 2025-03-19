import json
from pathlib import Path

from jsonschema import Draft4Validator

_REPO_PATH = Path(__file__).parent.parent
_SCHEMA_PATH = _REPO_PATH / "keyFiles" / "table_schema.json"


def test_table_schema_valid():
    """Test whether the table JSON schema is valid."""
    with _SCHEMA_PATH.open() as f:
        schema = json.load(f)

    Draft4Validator.check_schema(schema)
