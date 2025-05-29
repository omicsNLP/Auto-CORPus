"""Use regular expression for searching/replacing reference strings."""

import re
from dataclasses import dataclass
from typing import Any

from .data_structures import Paragraph


@dataclass
class ReferencesParagraph(Paragraph):
    """A paragraph for the references section of the article."""

    title: str = ""
    journal: str = ""
    volume: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return the dictionary representation of the ReferencesParagraph."""
        return {
            k: v
            for k, v in super().as_dict().items()
            if v or k not in ("title", "journal", "volume")
        }


def get_references(
    reference: dict[str, Any], section_heading: str
) -> ReferencesParagraph:
    """Retrieve a structured reference dictionary from a BS4 object and section heading.

    Args:
        reference: dictionary containing the references node
        section_heading: Section heading string
    Returns:
        A dictionary containing the structured reference information.
    """
    text = reference["node"].get_text().replace("Go to:", "").replace("\n", "")
    text = re.sub(r"\s{2,}", " ", text)
    ref_section = ReferencesParagraph(
        section_heading,
        "",
        text,
        [{"iao_name": "references section", "iao_id": "IAO:0000320"}],
    )

    for k, v in reference.items():
        if k != "node":
            setattr(ref_section, k, ". ".join(v))

    return ref_section
