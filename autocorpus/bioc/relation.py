"""This module defines the BioCRelation class."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from .node import BioCNode


@dataclass
class BioCRelation:
    """A class representing a BioC relation."""

    id: str = field(default_factory=str)
    infons: dict[str, str] = field(default_factory=dict)
    nodes: list[BioCNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the BioCRelation instance to a dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the BioCRelation instance.
        """
        return {
            "id": self.id,
            "infons": self.infons,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BioCRelation:
        """Create a BioCRelation instance from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing the relation data.

        Returns:
            BioCRelation: An instance of BioCRelation created from the dictionary.
        """
        from .node import BioCNode  # import inside to avoid circular import issues

        return cls(
            id=data.get("id", ""),
            infons=data.get("infons", {}),
            nodes=[BioCNode.from_dict(n) for n in data.get("nodes", [])],
        )

    def to_xml(self) -> ET.Element:
        """Convert the BioCRelation instance to an XML element.

        Returns:
            ET.Element: An XML element representation of the BioCRelation instance.
        """
        elem = ET.Element("relation", {"id": self.id})
        for k, v in self.infons.items():
            infon = ET.SubElement(elem, "infon", {"key": k})
            infon.text = v
        for node in self.nodes:
            elem.append(node.to_xml())
        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCRelation:
        """Create a BioCRelation instance from an XML element.

        Args:
            elem (ET.Element): An XML element containing the relation data.

        Returns:
            BioCRelation: An instance of BioCRelation created from the XML element.
        """
        from .node import BioCNode

        infons = {e.attrib["key"]: e.text for e in elem.findall("infon")}
        nodes = [BioCNode.from_xml(n) for n in elem.findall("node")]
        return cls(
            id=elem.attrib.get("id", ""),
            infons={k: v for k, v in infons.items() if v is not None},
            nodes=nodes,
        )
