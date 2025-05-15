# tests/bioc/test_bioc_collection.py

import xml.etree.ElementTree as ET

import pytest

from autocorpus.ac_bioc import (
    BioCCollection,
)


def test_to_dict(sample_collection):
    """Test the dictionary representation of a BioCCollection."""
    c = sample_collection.to_dict()
    assert c["source"] == "test_source"
    assert c["date"] == "2023-01-01"
    assert c["key"] == "abc123"
    assert c["infons"] == {"language": "en"}
    assert isinstance(c["documents"], list)
    assert c["documents"][0]["id"] == "doc1"


def test_to_json_matches_to_dict(sample_collection):
    """Test that the JSON representation of the collection matches its dictionary representation."""
    collection = sample_collection
    assert collection.to_json() == collection.to_dict()


def test_from_json(sample_collection):
    """Test creating a BioCCollection from JSON data."""
    json_data = sample_collection.to_dict()

    c = BioCCollection.from_json(json_data)
    assert c.source == "test_source"
    assert c.date == "2023-01-01"
    assert c.key == "abc123"
    assert c.infons == {"language": "en"}
    assert isinstance(c.documents, list)
    assert c.documents[0].id == "doc1"


def test_to_xml(sample_collection):
    """Test the XML representation of a BioCCollection."""
    collection = sample_collection
    xml_elem = collection.to_xml()
    assert xml_elem.tag == "collection"
    assert xml_elem.findtext("source") == "test_source"
    assert xml_elem.findtext("date") == "2023-01-01"
    assert xml_elem.findtext("key") == "abc123"
    assert xml_elem.find("infon").text == "en"
    assert len(xml_elem.findall("document")) == 1


def test_from_xml(sample_collection):
    """Test creating a BioCCollection from an XML element."""
    # Roundtrip: to_xml -> string -> fromstring -> from_xml
    collection = sample_collection
    xml_elem = collection.to_xml()
    xml_str = ET.tostring(xml_elem)
    parsed_elem = ET.fromstring(xml_str)

    new_collection = BioCCollection.from_xml(parsed_elem)
    assert new_collection.source == "test_source"
    assert new_collection.date == "2023-01-01"
    assert new_collection.key == "abc123"
    assert new_collection.infons == {"language": "en"}
    assert isinstance(new_collection.documents, list)
    assert new_collection.documents[0].id == "doc1"


def test_bioc_collection_dtd_validation(dtd_path, sample_collection):
    """Test that a BioCCollection's XML validates against the BioC DTD."""
    from lxml import etree as LET

    xml_elem = sample_collection.to_xml()

    # use ET import rather than lxml's ET, due to an error serializing directly with lxml
    xml_str = ET.tostring(xml_elem, encoding="utf-8", xml_declaration=True)

    # Parse the DTD file
    with open(dtd_path, "rb") as dtd_file:
        dtd = LET.DTD(dtd_file)

    doc = LET.fromstring(xml_str)
    print(doc.find("document"))

    assert dtd.validate(doc), dtd.error_log.filter_from_errors()
