from __future__ import annotations

import xml.etree.ElementTree as ET


class BioCLocation:
    """Represents a location in BioC format."""

    def __init__(self, offset: int, length: int):
        """Initialize a BioCLocation instance.

        Args:
            offset (int): The starting offset of the location.
            length (int): The length of the location.
        """
        self.offset = offset
        self.length = length

    def to_dict(self) -> dict[str, int]:
        """Convert the BioCLocation instance to a dictionary.

        Returns:
            dict[str, int]: A dictionary representation of the BioCLocation instance.
        """
        return {
            "offset": self.offset,
            "length": self.length,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> BioCLocation:
        """Create a BioCLocation instance from a dictionary.

        Args:
            cls (type): The class to instantiate.
            data (dict[str, int]): A dictionary containing the 'offset' and 'length' keys.
                If the keys are not present, default values of 0 will be used.

        Returns:
            BioCLocation: An instance of BioCLocation created from the dictionary.
        """
        return cls(
            offset=data.get("offset", 0),
            length=data.get("length", 0),
        )

    def to_xml(self) -> ET.Element:
        """Convert the BioCLocation instance to an XML element.

        Returns:
            ET.Element
                An XML element representation of the BioCLocation instance.
                The element will have 'offset' and 'length' attributes.
        """
        elem = ET.Element("location")
        elem.set("offset", str(self.offset))
        elem.set("length", str(self.length))
        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCLocation:
        """Create a BioCLocation instance from an XML element.

        Args:
            elem (ET.Element): An XML element with 'offset' and 'length' attributes.
                The attributes will be converted to integers.

        Returns:
            BioCLocation
                An instance of BioCLocation created from the XML element.
                If the attributes are not present, default values of 0 will be used.
        """
        offset = int(elem.attrib.get("offset", 0))
        length = int(elem.attrib.get("length", 0))
        return cls(offset=offset, length=length)
