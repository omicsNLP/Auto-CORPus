from __future__ import annotations

import xml.etree.ElementTree as ET


class BioCLocation:
    """Represents a location in BioC format."""

    def __init__(self, offset: int, length: int):
        """Initialize a BioCLocation instance.

        :param offset: The starting offset of the location.
        :param length: The length of the location.
        """
        self.offset = offset
        self.length = length

    def to_dict(self) -> dict[str, int]:
        """Convert the BioCLocation instance to a dictionary.

        :return: A dictionary with 'offset' and 'length' as keys.
        """
        return {
            "offset": self.offset,
            "length": self.length,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> BioCLocation:
        """Create a BioCLocation instance from a dictionary.

        :param data: A dictionary with 'offset' and 'length' as keys.
        :return: A BioCLocation instance.
        """
        return cls(
            offset=data.get("offset", 0),
            length=data.get("length", 0),
        )

    def to_xml(self) -> ET.Element:
        """Convert the BioCLocation instance to an XML element.

        :return: An XML element representing the location.
        """
        elem = ET.Element("location")
        elem.set("offset", str(self.offset))
        elem.set("length", str(self.length))
        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCLocation:
        """Create a BioCLocation instance from an XML element.

        :param elem: An XML element with 'offset' and 'length' attributes.
        :return: A BioCLocation instance.
        """
        offset = int(elem.attrib.get("offset", 0))
        length = int(elem.attrib.get("length", 0))
        return cls(offset=offset, length=length)
