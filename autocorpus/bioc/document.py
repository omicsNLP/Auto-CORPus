"""This module defines the BioCDocument class.

BioCDocument objects include a list of BioCPassage objects and provide a method to
convert the document to a dictionary representation.
"""

import xml.etree.ElementTree as ET
from typing import Any

from .annotation import BioCAnnotation
from .passage import BioCPassage
from .relation import BioCRelation


class BioCDocument:
    def __init__(
        self,
        id: str,
        inputfile: str = "",
        infons: dict[str, str] | None = None,
        passages: list[BioCPassage] | None = None,
        annotations: list[BioCAnnotation] | None = None,
        relations: list[BioCRelation] | None = None,
    ):
        self.id = id
        self.inputfile = inputfile
        self.infons = infons or {}
        self.passages = passages or []
        self.annotations = annotations or []
        self.relations = relations or []

    def to_dict(self):
        return {
            "id": self.id,
            "infons": self.infons,
            "passages": [p.to_dict() for p in self.passages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BioCDocument":
        passages = [BioCPassage.from_dict(p) for p in data.get("passages", [])]
        return cls(
            id=data["id"],
            infons=data.get("infons", {}),
            passages=passages,
            # You could also support annotations/relations here if needed
        )

    def to_json(self) -> dict[str, Any]:
        return self.to_dict()

    def to_xml(self) -> ET.Element:
        doc_elem = ET.Element("document")

        id_elem = ET.SubElement(doc_elem, "id")
        id_elem.text = self.id

        for k, v in self.infons.items():
            infon = ET.SubElement(doc_elem, "infon", {"key": k})
            infon.text = v

        for passage in self.passages:
            doc_elem.append(passage.to_xml())

        for ann in self.annotations:
            doc_elem.append(ann.to_xml())
        for rel in self.relations:
            doc_elem.append(rel.to_xml())

        return doc_elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "BioCDocument":
        id_text = elem.findtext("id", default="")

        infons = {
            e.attrib["key"]: e.text for e in elem.findall("infon") if e.text is not None
        }

        passages = [BioCPassage.from_xml(p_elem) for p_elem in elem.findall("passage")]

        return cls(
            id=id_text,
            infons=infons,
            passages=passages,
            # Again, add annotations/relations here when needed
        )
