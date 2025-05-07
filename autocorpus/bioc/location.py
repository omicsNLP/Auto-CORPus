import xml.etree.ElementTree as ET


class BioCLocation:
    def __init__(self, offset: int, length: int):
        self.offset = offset
        self.length = length

    def to_dict(self) -> dict:
        return {
            "offset": self.offset,
            "length": self.length,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BioCLocation":
        return cls(
            offset=data.get("offset", 0),
            length=data.get("length", 0),
        )

    def to_xml(self) -> ET.Element:
        elem = ET.Element("location")
        elem.set("offset", str(self.offset))
        elem.set("length", str(self.length))
        return elem

    @classmethod
    def from_xml(cls, elem: ET.Element) -> "BioCLocation":
        offset = int(elem.attrib.get("offset", 0))
        length = int(elem.attrib.get("length", 0))
        return cls(offset=offset, length=length)
