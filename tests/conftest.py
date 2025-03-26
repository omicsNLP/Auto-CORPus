"""Fixtures for tests."""

from pathlib import Path

import pytest


@pytest.fixture
def data_path() -> Path:
    """The path to the folder containing test data files."""
    return Path(__file__).parent / "data"
