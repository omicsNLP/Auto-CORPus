"""This module defines the BioC class.

BioC extends BioC to include additional functionality for handling  data, such as
column headings and data sections.
"""

from typing import Any
from .key import BioCKey
from .sentence import BioCSentence
from .annotation import BioCAnnotation
from .relation import BioCRelation


class BioCPassage:
    def __init__(
        self,
        text: str = "",
        offset: int = 0,
        infons: dict[str, str] | None = None,
        sentences: list[BioCSentence] | None = None,
        annotations: list[BioCAnnotation] | None = None,
        relations: list[BioCRelation] | None = None,
    ):
        self.text = text
        self.offset = offset
        self.infons = infons or {}
        self.sentences = sentences or []
        self.annotations = annotations or []
        self.relations = relations or []

    def to_dict(self):
        return {
            "text": self.text,
            "offset": self.offset,
            "infons": self.infons,
            "sentences": [s.to_dict() for s in self.sentences],
        }
