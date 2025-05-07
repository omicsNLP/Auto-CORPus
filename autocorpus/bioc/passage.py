"""This module defines the BioC class.

BioC extends BioC to include additional functionality for handling  data, such as
column headings and data sections.
"""

import xml.etree.ElementTree as ET

from .annotation import BioCAnnotation
from .relation import BioCRelation
from .sentence import BioCSentence


class BioCPassage:
    def __init__(
        self,
        text: str = "",
        offset: int = 0,
        infons: dict[str, str] | None = None,
        sentences: list[BioCSentence] | None = None,
        annotations: list[BioCAnnotation] | None = None,
        relations: list[BioCRelation] | None = None,
    ):
        self.text = text
        self.offset = offset
        self.infons = infons or {}
        self.sentences = sentences or []
        self.annotations = annotations or []
        self.relations = relations or []

    def to_dict(self):
        return {
            "text": self.text,
            "offset": self.offset,
            "infons": self.infons,
            "sentences": [s.to_dict() for s in self.sentences],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BioCPassage":
        sentences = [BioCSentence.from_dict(s) for s in data.get("sentences", [])]
        return cls(
            text=data.get("text", ""),
            offset=data.get("offset", 0),
            infons=data.get("infons", {}),
            sentences=sentences,
        )

    def to_json(self) -> dict:
        return self.to_dict()

    def to_xml(self) -> ET.Element:
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
    def from_xml(cls, elem: ET.Element) -> "BioCPassage":
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
