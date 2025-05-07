import json
import xml.etree.ElementTree as ET

from .collection import BioCCollection


class BioCJSON:
    """JSON deserialization for BioC objects."""

    @staticmethod
    def loads(json_str: str) -> BioCCollection:
        data = json.loads(json_str)
        return BioCCollection.from_json(data)


class BioCXML:
    """XML deserialization for BioC objects."""

    @staticmethod
    def loads(xml_str: str) -> BioCCollection:
        root = ET.fromstring(xml_str)
        return BioCCollection.from_xml(root)
