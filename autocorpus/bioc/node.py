import xml.etree.ElementTree as ET


class BioCNode:
    def __init__(self, refid: str, role: str | None = None):
        self.refid = refid
        self.role = role or ""

    def to_dict(self) -> dict:
        return {
            "refid": self.refid,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BioCNode":
        return cls(
            refid=data.get("refid", ""),
            role=data.get("role", ""),
        )

    def to_xml(self) -> ET.Element:
        elem = ET.Element("node")
        elem.set("refid", self.refid)
        elem.set("role", self.role)
        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "BioCNode":
        return cls(
            refid=elem.attrib.get("refid", ""),
            role=elem.attrib.get("role", ""),
        )
