"""BioC Passage builder script."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

_DEFAULT_KEYS = set(("section_heading", "subsection_heading", "body", "section_type"))


@dataclass(frozen=True)
class BioCPassage:
    """Represents a BioC passage."""

    offset: int
    infons: dict[str, Any]
    text: str

    @classmethod
    def from_dict(cls, passage: dict[str, Any], offset: int) -> BioCPassage:
        """Create a BioCPassage from a passage dict and an offset.

        Args:
            passage: dict containing info about passage
            offset: Passage offset

        Returns:
            BioCPassage object
        """
        infons = {k: v for k, v in passage.items() if k not in _DEFAULT_KEYS}

        # TODO: Doesn't account for subsubsection headings which might exist
        if heading := passage.get("section_heading", None):
            infons["section_title_1"] = heading
        if subheading := passage.get("subsection_heading", None):
            infons["section_title_2"] = subheading
        for i, section_type in enumerate(passage["section_type"]):
            infons[f"iao_name_{i + 1}"] = section_type["iao_name"]
            infons[f"iao_id_{i + 1}"] = section_type["iao_id"]

        return cls(offset, infons, passage["body"])

    @classmethod
    def from_title(cls, title: str, offset: int) -> BioCPassage:
        """Create a BioCPassage from a title and offset.

        Args:
            title: Passage title
            offset: Passage offset

        Returns:
            BioCPassage object
        """
        infons = {"iao_name_1": "document title", "iao_id_1": "IAO:0000305"}
        return cls(offset, infons, title)

    def as_dict(self) -> dict[str, Any]:
        """Convert this class to a dict."""
        return asdict(self) | {
            "sentences": [],
            "annotations": [],
            "relations": [],
        }
