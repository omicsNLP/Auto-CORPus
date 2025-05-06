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
