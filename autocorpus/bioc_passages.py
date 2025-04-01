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

        # TODO: currently assumes section_heading and subsection_heading will always
        # exist, should ideally check for existence. Also doesn't account for
        # subsubsection headings which might exist
        if passage["section_heading"] != "":
            infons["section_title_1"] = passage["section_heading"]
        if passage["subsection_heading"] != "":
            infons["section_title_2"] = passage["subsection_heading"]
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
        title_passage = {
            "section_heading": "",
            "subsection_heading": "",
            "body": title,
            "section_type": [{"iao_name": "document title", "iao_id": "IAO:0000305"}],
        }
        return cls.from_dict(title_passage, offset)

    def as_dict(self) -> dict[str, Any]:
        """Convert this class to a dict."""
        return asdict(self) | {
            "sentences": [],
            "annotations": [],
            "relations": [],
        }
