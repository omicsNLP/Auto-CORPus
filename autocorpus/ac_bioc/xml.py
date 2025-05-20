"""This module provides XML serialization and deserialization for BioC objects."""

import xml.etree.ElementTree as ET

from .collection import BioCCollection


class BioCXML:
    """XML serialization for BioC objects."""

    @staticmethod
    def dumps(collection: BioCCollection) -> str:
        """Serialize a BioCCollection object to an XML string.

        Args:
            collection (BioCCollection): The BioCCollection object to serialize.

        Returns:
            str: The XML string representation of the collection.
        """
        root = collection.to_xml()
        return ET.tostring(root, encoding="unicode")

    @staticmethod
    def loads(xml_str: str) -> BioCCollection:
        """Deserialize an XML string into a BioCCollection object.

        Args:
            xml_str (str): The XML string to deserialize.

        Returns:
            BioCCollection: The deserialized BioCCollection object.
        """
        root = ET.fromstring(xml_str)
        return BioCCollection.from_xml(root)
