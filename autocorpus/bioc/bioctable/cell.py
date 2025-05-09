"""This module defines the BioCTableCell class."""

from dataclasses import dataclass, field


@dataclass
class BioCTableCell:
    """Represents a cell in a table."""

    cell_id: str = field(default_factory=str)
    cell_text: str = field(default_factory=str)

    def to_dict(self) -> dict[str, str]:
        """Convert the cell's attributes to a dictionary.

        Returns:
            dict[str, str]
                A dictionary containing the cell's ID and text content.
        """
        return {"cell_id": self.cell_id, "cell_text": self.cell_text}
