"""This module defines the BioCTableCell class."""


class BioCTableCell:
    """Represents a cell in a BioC table.

    Attributes:
        cell_id : str
            The unique identifier for the cell.
        cell_text : str
            The text content of the cell.

    Methods:
        to_dict() -> dict[str, str]
            Converts the cell's attributes to a dictionary.
    """

    def __init__(self, cell_id: str, cell_text: str):
        """Initialize a BioCTableCell with an ID and text content.

        Args:
            cell_id (str): The unique identifier for the cell.
            cell_text (str): The text content of the cell.
        """
        self.cell_id: str = cell_id
        self.cell_text: str = cell_text

    def to_dict(self) -> dict[str, str]:
        """Convert the cell's attributes to a dictionary.

        Returns:
            dict[str, str]
                A dictionary containing the cell's ID and text content.
        """
        return {"cell_id": self.cell_id, "cell_text": self.cell_text}
