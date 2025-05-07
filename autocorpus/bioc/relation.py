import xml.etree.ElementTree as ET
from typing import Any

from .node import BioCNode


class BioCRelation:
    def __init__(
        self,
        id: str | None = None,
        infons: dict[str, str] | None = None,
        nodes: list[BioCNode] | None = None,
    ):
        self.id = id or ""
        self.infons = infons or {}
        self.nodes = nodes or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "infons": self.infons,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BioCRelation":
        from .node import BioCNode  # import inside to avoid circular import issues

        return cls(
            id=data.get("id", ""),
            infons=data.get("infons", {}),
            nodes=[BioCNode.from_dict(n) for n in data.get("nodes", [])],
        )

    def to_xml(self) -> ET.Element:
        elem = ET.Element("relation", {"id": self.id})
        for k, v in self.infons.items():
            infon = ET.SubElement(elem, "infon", {"key": k})
            infon.text = v
        for node in self.nodes:
            elem.append(node.to_xml())
        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "BioCRelation":
        from .node import BioCNode

        infons = {e.attrib["key"]: e.text for e in elem.findall("infon")}
        nodes = [BioCNode.from_xml(n) for n in elem.findall("node")]
        return cls(
            id=elem.attrib.get("id", ""),
            infons={k: v for k, v in infons.items() if v is not None},
            nodes=nodes,
        )
