"""This module defines the BioCDocument class.

BioCDocument objects include a list of BioCPassage objects and provide a method to
convert the document to a dictionary representation.
"""

from .annotation import BioCAnnotation
from .key import BioCKey
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
