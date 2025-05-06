from .location import BioCLocation


class BioCAnnotation:
    def __init__(
        self,
        id: str,
        text: str,
        offset: int,
        length: int,
        infons: dict[str, str] | None = None,
        locations: list[BioCLocation] | None = None,
    ):
        self.id = id
        self.text = text
        self.offset = offset
        self.length = length
        self.infons = infons or {}
        self.locations = locations or []

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "offset": self.offset,
            "length": self.length,
            "infons": self.infons,
        }
