"""Module to define common data structures for autocorpus."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Paragraph:
    """A paragraph for a section of the article."""

    section_heading: str
    subsection_heading: str
    body: str
    section_type: list[dict[str, str]]

    def as_dict(self) -> dict[str, Any]:
        """Return the dictionary representation of the Paragraph."""
        return asdict(self)


@dataclass(frozen=True)
class SectionChild:
    """A child node in the section."""

    subheading: str
    body: str
