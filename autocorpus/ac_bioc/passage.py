"""This module defines the BioC class.

BioC extends BioC to include additional functionality for handling  data, such as
column headings and data sections.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from dataclasses_json import DataClassJsonMixin, dataclass_json

from .annotation import BioCAnnotation
from .relation import BioCRelation
from .sentence import BioCSentence

_DEFAULT_KEYS = set(
    ("section_heading", "subsection_heading", "body", "section_type", "offset")
)


@dataclass_json
@dataclass
class BioCPassage(DataClassJsonMixin):
    """Represents a passage in a BioC document."""

    text: str = field(default_factory=str)
    offset: int = field(default_factory=int)
    infons: dict[str, Any] = field(default_factory=dict)
    sentences: list[BioCSentence] = field(default_factory=list)
    annotations: list[BioCAnnotation] = field(default_factory=list)
    relations: list[BioCRelation] = field(default_factory=list)

    @classmethod
    def from_ac_dict(cls, passage: dict[str, Any]) -> BioCPassage:
        """Create a BioCPassage from a passage dict and an offset.

        Args:
            passage: dict containing info about passage

        Returns:
            BioCPassage object
        """
        infons = {k: v for k, v in passage.items() if k not in _DEFAULT_KEYS}
        # TODO: Doesn't account for subsubsection headings which might exist
        if heading := passage.get("section_heading", None):
            infons["section_title_1"] = heading
        if subheading := passage.get("subsection_heading", None):
            infons["section_title_2"] = subheading
        for i, section_type in enumerate(passage["section_type"]):
            infons[f"iao_name_{i + 1}"] = section_type["iao_name"]
            infons[f"iao_id_{i + 1}"] = section_type["iao_id"]

        return cls(offset=passage.get("offset", 0), infons=infons, text=passage["body"])

    @classmethod
    def from_title(cls, title: str, offset: int) -> BioCPassage:
        """Create a BioCPassage from a title and offset.

        Args:
            title: Passage title
            offset: Passage offset

        Returns:
            BioCPassage object
        """
        infons = {"iao_name_1": "document title", "iao_id_1": "IAO:0000305"}
        return cls(offset=offset, infons=infons, text=title)

    def to_xml(self) -> ET.Element:
        """Convert the BioCPassage instance to an XML element.

        Returns:
            ET.Element: An XML element representation of the BioCPassage instance.
        """
        passage_elem = ET.Element("passage")

        for k, v in self.infons.items():
            infon = ET.SubElement(passage_elem, "infon", {"key": k})
            infon.text = v

        offset_elem = ET.SubElement(passage_elem, "offset")
        offset_elem.text = str(self.offset)

        text_elem = ET.SubElement(passage_elem, "text")
        text_elem.text = self.text

        for sentence in self.sentences:
            passage_elem.append(sentence.to_xml())

        return passage_elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCPassage:
        """Create a BioCPassage instance from an XML element.

        Args:
            elem (ET.Element): An XML element representing a passage.

        Returns:
            BioCPassage: An instance of BioCPassage populated with the provided XML data.
        """
        offset = int(elem.findtext("offset", default="0"))
        text = elem.findtext("text", default="")

        infons = {
            e.attrib["key"]: e.text for e in elem.findall("infon") if e.text is not None
        }

        sentences = [
            BioCSentence.from_xml(s_elem) for s_elem in elem.findall("sentence")
        ]

        return cls(
            text=text,
            offset=offset,
            infons=infons,
            sentences=sentences,
        )
