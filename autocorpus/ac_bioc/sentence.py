"""This module defines the BioCSentence class."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from .annotation import BioCAnnotation
from .relation import BioCRelation


@dataclass
class BioCSentence:
    """Represents a sentence in the BioC format."""

    text: str
    offset: int
    infons: dict[str, str] = field(default_factory=dict)
    annotations: list[BioCAnnotation] = field(default_factory=list)
    relations: list[BioCRelation] = field(default_factory=list)

    def to_dict(self):
        """Convert the BioCSentence instance to a dictionary representation.

        Returns:
            dict: A dictionary containing the sentence's text, offset, infons, and annotations.
        """
        return {
            "text": self.text,
            "offset": self.offset,
            "infons": self.infons,
            "annotations": [a.to_dict() for a in self.annotations],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BioCSentence:
        """Create a BioCSentence instance from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing sentence data.

        Returns:
            BioCSentence: An instance of BioCSentence created from the dictionary.
        """
        annotations = [BioCAnnotation.from_dict(a) for a in data.get("annotations", [])]
        return cls(
            text=data.get("text", ""),
            offset=data.get("offset", 0),
            infons=data.get("infons", {}),
            annotations=annotations,
        )

    def to_json(self) -> dict[str, Any]:
        """Convert the BioCSentence instance to a JSON-compatible dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the sentence.
        """
        return self.to_dict()

    def to_xml(self) -> ET.Element:
        """Convert the BioCSentence instance to an XML element.

        Returns:
            ET.Element: An XML element representing the sentence.
        """
        sentence_elem = ET.Element("sentence")

        for k, v in self.infons.items():
            infon = ET.SubElement(sentence_elem, "infon", {"key": k})
            infon.text = v

        offset_elem = ET.SubElement(sentence_elem, "offset")
        offset_elem.text = str(self.offset)

        text_elem = ET.SubElement(sentence_elem, "text")
        text_elem.text = self.text

        for ann in self.annotations:
            sentence_elem.append(ann.to_xml())

        return sentence_elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCSentence:
        """Create a BioCSentence instance from an XML element.

        Args:
            elem (ET.Element): An XML element representing a sentence.

        Returns:
            BioCSentence: An instance of BioCSentence created from the XML element.
        """
        offset = int(elem.findtext("offset", default="0"))
        text = elem.findtext("text", default="")

        infons = {
            e.attrib["key"]: e.text for e in elem.findall("infon") if e.text is not None
        }

        annotations = [
            BioCAnnotation.from_xml(a_elem) for a_elem in elem.findall("annotation")
        ]

        return cls(
            text=text,
            offset=offset,
            infons=infons,
            annotations=annotations,
        )
