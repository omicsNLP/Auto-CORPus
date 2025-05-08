"""This module defines the BioCNode class."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class BioCNode:
    """Represents a node in a BioC graph with a reference ID and a role."""

    def __init__(self, refid: str, role: str = field(default_factory=str)):
        """Initialize a BioCNode instance.

        Args:
            refid (str): The reference ID of the node.
            role (str): The role of the node. Defaults to an empty string.
        """
        self.refid = refid
        self.role = role

    def to_dict(self) -> dict[str, str]:
        """Convert the BioCNode instance to a dictionary representation."""
        return {
            "refid": self.refid,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> BioCNode:
        """Create a BioCNode instance from a dictionary.

        Args:
            data (dict[str, str]): A dictionary containing 'refid' and 'role' keys.

        Returns:
            BioCNode: An instance of BioCNode initialized with the provided data.
        """
        return cls(
            refid=data.get("refid", ""),
            role=data.get("role", ""),
        )

    def to_xml(self) -> ET.Element:
        """Convert the BioCNode instance to an XML element.

        Returns:
            ET.Element: An XML element representing the BioCNode instance.
        """
        elem = ET.Element("node")
        elem.set("refid", self.refid)
        elem.set("role", self.role)
        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> BioCNode:
        """Create a BioCNode instance from an XML element.

        Args:
            elem (ET.Element): An XML element containing 'refid' and 'role' attributes.

        Returns:
            BioCNode: An instance of BioCNode initialized with the provided XML data.
        """
        return cls(
            refid=elem.attrib.get("refid", ""),
            role=elem.attrib.get("role", ""),
        )
