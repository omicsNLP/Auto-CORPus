"""This module defines the BioCTablePassage class."""

from dataclasses import dataclass, field
from typing import Any

from ...ac_bioc import BioCPassage
from .cell import BioCTableCell


@dataclass
class BioCTablePassage(BioCPassage):
    """A class that extends BioCPassage to handle table data."""

    column_headings: list[BioCTableCell] = field(default_factory=list)
    data_section: list[dict[str, Any]] = field(default_factory=list)
