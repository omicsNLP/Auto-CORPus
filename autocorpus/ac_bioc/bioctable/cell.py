"""This module defines the BioCTableCell class."""

from dataclasses import dataclass, field


@dataclass
class BioCTableCell:
    """Represents a cell in a table."""

    cell_id: str = field(default_factory=str)
    cell_text: str = field(default_factory=str)
