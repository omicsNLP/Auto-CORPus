"""Use regular expression for searching/replacing reference strings."""

import re
from typing import Any


def get_reference(reference: dict[str, Any], section_heading: str) -> dict[str, Any]:
    """Retrieve a structured reference dictionary from a BeautifulSoup object and section heading.

    Args:
        reference: BeautifulSoup object
        section_heading: Section heading string
    Returns:
        A dictionary containing the structured reference information.
    """
    text = reference["node"].get_text().replace("Go to:", "").replace("\n", "")
    text = re.sub(r"\s{2,}", " ", text)
    ref_section = {
        "section_heading": section_heading,
        "subsection_heading": "",
        "body": text,
        "section_type": [{"iao_name": "references section", "iao_id": "IAO:0000320"}],
    }

    for sub_sec in reference:
        if sub_sec == "node":
            continue
        ref_section[sub_sec] = ". ".join(reference[sub_sec])

    return ref_section
