"""This module provides deserialization functionality for BioC objects.

It includes classes for handling JSON and XML formats and converting them
into BioCCollection objects.
"""

import json
import xml.etree.ElementTree as ET

from .collection import BioCCollection


class BioCJSON:
    """JSON deserialization for BioC objects."""

    @staticmethod
    def loads(json_str: str) -> BioCCollection:
        """Deserialize a BioC JSON string into a BioCCollection object.

        Args:
            json_str (str): A string containing BioC JSON data.

        Returns:
            BioCCollection: The deserialized BioCCollection object.
        """
        data = json.loads(json_str)
        return BioCCollection.from_json(data)


class BioCXML:
    """XML deserialization for BioC objects."""

    @staticmethod
    def loads(xml_str: str) -> BioCCollection:
        """Deserialize a BioC XML string into a BioCCollection object.

        Args:
            xml_str (str): A string containing BioC XML data.

        Returns:
            BioCCollection: The deserialized BioCCollection object.
        """
        root = ET.fromstring(xml_str)
        return BioCCollection.from_xml(root)
