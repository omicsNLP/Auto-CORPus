"""This module defines the BioCTableCollection class."""

from dataclasses import dataclass, field

from ...ac_bioc import BioCCollection, BioCDocument


@dataclass
class BioCTableCollection(BioCCollection):
    """A collection of BioCTableDocument objects extending BioCCollection."""

    documents: list[BioCDocument] = field(default_factory=list)
