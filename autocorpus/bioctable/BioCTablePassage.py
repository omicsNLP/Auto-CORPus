"""This module defines the BioCTablePassage class.

BioCTablePassage extends BioCPassage to include additional functionality for handling table data, such as
column headings and data sections.
"""

from typing import Any

from bioc import BioCPassage

from .BioCTableCell import BioCTableCell


class BioCTablePassage(BioCPassage):
    """A class that extends BioCPassage to handle table data.

    Attributes:
        column_headings : list[BioCTableCell]
            A list of cells representing the column headings of the table.
        data_section : list[dict[str, Any]]
            A list of dictionaries representing the data sections of the table.

    Methods:
        to_dict() -> dict[str, Any]
            Converts the BioCTablePassage instance to a dictionary representation.
    """

    def __init__(self, *args, **kwargs):
        """Initialize a BioCTablePassage instance.

        Args:
            *args: Variable length argument list passed to the parent class.
            **kwargs: Arbitrary keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.column_headings: list[BioCTableCell] = []
        self.data_section: list[dict[str, Any]] = []

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
            for row in section.get("data_rows", []):
                serialized_row = [cell.to_dict() for cell in row]
                serialized_section["data_rows"].append(serialized_row)
            data_section_serialized.append(serialized_section)

        base["data_section"] = data_section_serialized
        return base
