"""This module defines the BioCTablePassage class."""

from dataclasses import dataclass, field
from typing import Any

from ...bioc import BioCPassage
from .cell import BioCTableCell


@dataclass
class BioCTablePassage(BioCPassage):
    """A class that extends BioCPassage to handle table data."""

    column_headings: list[BioCTableCell] = field(default_factory=list)
    data_section: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the BioCTablePassage instance to a dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the BioCTablePassage instance,
            including column headings and data sections.
        """
        base = super().to_dict()
        base["column_headings"] = [cell.to_dict() for cell in self.column_headings]

        # Convert data_section cells too
        data_section_serialized = []
        for section in self.data_section:
            serialized_section = {
                "table_section_title_1": section.get("table_section_title_1", ""),
                "data_rows": [],
            }
            for row in section["data_rows"]:
                serialized_row = [cell.to_dict() for cell in row]
                serialized_section["data_rows"].append(serialized_row)
            data_section_serialized.append(serialized_section)
        base["data_section"] = data_section_serialized
        return base
