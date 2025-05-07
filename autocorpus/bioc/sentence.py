from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .annotation import BioCAnnotation
from .relation import BioCRelation


class BioCSentence:
    def __init__(
        self,
        text: str,
        offset: int,
        infons: dict[str, str] | None = None,
        annotations: list[BioCAnnotation] | None = None,
        relations: list[BioCRelation] | None = None,
    ):
        self.text = text
        self.offset = offset
        self.infons = infons or {}
        self.annotations = annotations or []
        self.relations = relations or []

    def to_dict(self):
        return {
            "text": self.text,
            "offset": self.offset,
            "infons": self.infons,
            "annotations": [a.to_dict() for a in self.annotations],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BioCSentence:
        annotations = [BioCAnnotation.from_dict(a) for a in data.get("annotations", [])]
        return cls(
            text=data.get("text", ""),
            offset=data.get("offset", 0),
            infons=data.get("infons", {}),
            annotations=annotations,
        )

    def to_json(self) -> dict[str, Any]:
        return self.to_dict()

    def to_xml(self) -> ET.Element:
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
