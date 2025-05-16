"""Fixtures for tests."""

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
