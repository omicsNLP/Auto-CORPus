"""Fixtures for tests."""

import sys
from pathlib import Path

import pytest

from autocorpus.ac_bioc import (
    BioCAnnotation,
    BioCCollection,
    BioCDocument,
    BioCLocation,
    BioCNode,
    BioCPassage,
    BioCRelation,
)


@pytest.fixture
def data_path() -> Path:
    """The path to the folder containing test data files."""
    return Path(__file__).parent / "data"


@pytest.fixture
def dtd_path(data_path) -> Path:
    """Fixture that provides the path to the DTD file."""
    return data_path / "BioC.dtd"


@pytest.fixture
def sample_collection() -> BioCCollection:
    """Fixture that provides a sample BioCDocument for testing."""
    return BioCCollection(
        source="test_source",
        date="2023-01-01",
        key="abc123",
        infons={"language": "en"},
        documents=[
            BioCDocument(
                id="doc1",
                infons={"title": "Test Title"},
                passages=[
                    BioCPassage(
                        text="Hello",
                        offset=0,
                        annotations=[
                            BioCAnnotation(
                                id="a1",
                                infons={"type": "gene"},
                                text="GeneA",
                                locations=[
                                    BioCLocation(offset=0, length=5),
                                ],
                            ),
                            BioCAnnotation(
                                id="a2",
                                infons={"type": "gene"},
                                text="GeneB",
                                locations=[
                                    BioCLocation(offset=6, length=5),
                                ],
                            ),
                        ],
                    ),
                ],
                relations=[
                    BioCRelation(
                        id="r1",
                        infons={"type": "relation"},
                        nodes=[
                            BioCNode(refid="a1", role="subject"),
                            BioCNode(refid="a2", role="object"),
                        ],
                    )
                ],
            )
        ],
    )


def pytest_addoption(parser):
    """Fixture to add command line options for pytest."""
    parser.addoption(
        "--ci",
        action="store_true",
        default=False,
        help="Indicate tests are running in CI",
    )


def pytest_configure(config):
    """Fixture to add custom markers to pytest."""
    config.addinivalue_line(
        "markers", "skip_ci_macos: mark test as unable to run in CI on MacOS"
    )


def pytest_collection_modifyitems(config, items):
    """Fixture to modify test collection based on command line options."""
    if not config.getoption("--ci"):
        # `--ci` not given in cli: this is not a CI run
        return
    skip_ci_macos = pytest.mark.skipif(
        sys.platform == "darwin", reason="Uses too much memory in CI on MacOS"
    )
    for item in items:
        if "skip_ci_macos" in item.keywords:
            item.add_marker(skip_ci_macos)
