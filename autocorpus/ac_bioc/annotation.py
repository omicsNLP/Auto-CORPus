"""This module defines the BioCAnnotation class."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from .location import BioCLocation


@dataclass
class BioCAnnotation:
    """Represents an annotation in a BioC document."""

    id: str = field(default_factory=str)
    text: str = field(default_factory=str)
    offset: int = field(default_factory=int)
    length: int = field(default_factory=int)
    infons: dict[str, str] = field(default_factory=dict)
    locations: list[BioCLocation] = field(default_factory=list)

    def to_dict(self):
        """Convert the annotation to a dictionary representation.

        Returns:
            dict: A dictionary containing the annotation's id, text, offset, length, and infons.
        """
        return {
            "id": self.id,
            "text": self.text,
            "offset": self.offset,
            "length": self.length,
            "infons": self.infons,
        }

    def to_json(self) -> dict[str, Any]:
        """Convert the annotation to a JSON-serializable dictionary.

        Returns:
            dict[str, Any]: A dictionary containing the annotation's id, text, offset, length, infons, and locations.
        """
        return {
            "id": self.id,
            "text": self.text,
            "offset": self.offset,
            "length": self.length,
            "infons": self.infons,
            "locations": [loc.to_dict() for loc in self.locations],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BioCAnnotation:
        """Create a BioCAnnotation instance from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing annotation data.

        Returns:
            BioCAnnotation: An instance of BioCAnnotation created from the dictionary.
        """
        from .location import BioCLocation  # Prevent circular imports

        locations = [BioCLocation.from_dict(loc) for loc in data.get("locations", [])]

        return cls(
            id=data["id"],
            text=data.get("text", ""),
            offset=data.get("offset", 0),
            length=data.get("length", 0),
            infons=data.get("infons", {}),
            locations=locations,
        )

    def to_xml(self) -> ET.Element:
        """Convert the annotation to an XML element.

        Returns:
            ET.Element: An XML element representing the annotation.
        """
        annotation_elem = ET.Element("annotation")
        annotation_elem.set("id", self.id)

        for k, v in self.infons.items():
            infon = ET.SubElement(annotation_elem, "infon", {"key": k})
            infon.text = v

        for loc in self.locations:
            annotation_elem.append(loc.to_xml())

        text_elem = ET.SubElement(annotation_elem, "text")
        text_elem.text = self.text

        return annotation_elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCAnnotation:
        """Create a BioCAnnotation instance from an XML element.

        Args:
            elem (ET.Element): An XML element representing the annotation.

        Returns:
            BioCAnnotation: An instance of BioCAnnotation created from the XML element.
        """
        from .location import BioCLocation  # Again, avoid circular imports

        id_ = elem.attrib.get("id", "")
        text = elem.findtext("text", default="")

        infons = {
            e.attrib["key"]: e.text for e in elem.findall("infon") if e.text is not None
        }

        locations = [
            BioCLocation.from_xml(loc_elem) for loc_elem in elem.findall("location")
        ]

        # Offset and length can be derived if needed from locations
        offset = int(locations[0].offset) if locations else 0
        length = int(locations[0].length) if locations else 0

        return cls(
            id=id_,
            text=text,
            offset=offset,
            length=length,
            infons=infons,
            locations=locations,
        )
