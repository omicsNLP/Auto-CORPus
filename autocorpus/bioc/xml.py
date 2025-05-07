import xml.etree.ElementTree as ET

from .collection import BioCCollection


class BioCXML:
    """XML serialization for BioC objects."""

    @staticmethod
    def dumps(collection: BioCCollection) -> str:
        root = collection.to_xml()
        return ET.tostring(root, encoding="unicode")

    @staticmethod
    def loads(xml_str: str) -> BioCCollection:
        root = ET.fromstring(xml_str)
        return BioCCollection.from_xml(root)
