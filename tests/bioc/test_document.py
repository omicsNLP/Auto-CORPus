# tests/bioc/test_bioc_document.py

import xml.etree.ElementTree as ET

import pytest

from autocorpus.ac_bioc import (
    BioCDocument,
    BioCNode,
    BioCPassage,
    BioCRelation,
)


@pytest.fixture
def sample_document():
    """Fixture that provides a sample BioCDocument for testing."""
    return BioCDocument(
        id="doc1",
        infons={"title": "Test Title"},
        passages=[BioCPassage(text="Hello", offset=0)],
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


def test_to_dict(sample_document):
    """Test the to_dict method of BioCDocument."""
    d = sample_document.to_dict()
    assert d["id"] == "doc1"
    assert d["infons"] == {"title": "Test Title"}
    assert isinstance(d["passages"], list)
    assert d["passages"][0]["text"] == "Hello"


def test_to_json_matches_to_dict(sample_document):
    """Test that the to_json method produces the same output as to_dict."""
    assert sample_document.to_json() == sample_document.to_dict()


def test_from_dict():
    """Test the from_dict method of BioCDocument."""
    data = {
        "id": "doc1",
        "infons": {"title": "Test Title"},
        "passages": [{"text": "Hello", "offset": 0}],
        "relations": [
            {
                "id": "r1",
                "infons": {"type": "relation"},
                "nodes": [
                    {
                        "refid": "a1",
                        "role": "subject",
                    },
                    {
                        "refid": "a2",
                        "role": "object",
                    },
                ],
            }
        ],
    }

    doc = BioCDocument.from_dict(data)
    assert doc.id == "doc1"
    assert doc.infons["title"] == "Test Title"
    assert len(doc.passages) == 1
    assert doc.passages[0].text == "Hello"


def test_to_xml(sample_document):
    """Test the to_xml method of BioCDocument."""
    xml_elem = sample_document.to_xml()
    assert xml_elem.tag == "document"
    assert xml_elem.findtext("id") == "doc1"
    assert xml_elem.find("infon").text == "Test Title"
    assert xml_elem.find("passage") is not None
    assert xml_elem.find("relation") is not None


def test_from_xml():
    """Test the from_xml method of BioCDocument."""
    # Constructing XML manually for a minimal document
    xml_str = """
    <document>
        <id>doc1</id>
        <infon key="title">Test Title</infon>
        <passage>
            <text>Hello</text>
            <offset>0</offset>
        </passage>
    </document>
    """
    elem = ET.fromstring(xml_str)

    doc = BioCDocument.from_xml(elem)
    assert doc.id == "doc1"
    assert doc.infons["title"] == "Test Title"
    assert len(doc.passages) == 1
    assert doc.passages[0].text == "Hello"
