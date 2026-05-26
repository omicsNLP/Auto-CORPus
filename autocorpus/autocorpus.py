"""The Auto-CORPus primary dataclass is defined in this module."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ac_bioc import BioCJSON, BioCXML
from .ac_bioc.collection import BioCCollection
from .bioc_formatter import get_formatted_bioc_collection


@dataclass
class Autocorpus:
    """Dataclass for a collection of BioC formatted text, tables and abbreviations."""

    file_path: Path
    main_text: dict[str, Any]
    abbreviations: dict[str, Any]
    tables: dict[str, Any] = field(default_factory=dict)

    @property
    def has_tables(self) -> bool:
        """Check if the Autocorpus has any tables.

        Returns:
            True if there are tables, False otherwise.
        """
        return bool(self.tables.get("documents"))

    def to_bioc(self) -> BioCCollection:
        """Get the currently loaded bioc as a dict.

        Returns:
            bioc as a BioCCollection object
        """
        return get_formatted_bioc_collection(self.main_text, self.file_path)

    def main_text_to_bioc_json(self) -> str:
        """Get the currently loaded main text as BioC JSON.

        Args:
            indent: level of indentation

        Returns:
            main text as BioC JSON
        """
        return get_formatted_bioc_collection(self.main_text, self.file_path).to_json(
            indent=2, ensure_ascii=False
        )

    def main_text_to_bioc_xml(self) -> str:
        """Get the currently loaded main text as BioC XML.

        Returns:
            main text as BioC XML
        """
        collection = BioCJSON.loads(
            json.dumps(
                get_formatted_bioc_collection(self.main_text, self.file_path),
                indent=2,
                ensure_ascii=False,
            )
        )
        return BioCXML.dumps(collection)

    def tables_to_bioc_json(self, indent: int = 2) -> str:
        """Get the currently loaded tables as Tables-JSON.

        Args:
            indent: level of indentation

        Returns:
            tables as Tables-JSON
        """
        return json.dumps(self.tables, ensure_ascii=False, indent=indent)

    def abbreviations_to_bioc_json(self, indent: int = 2) -> str:
        """Get the currently loaded abbreviations as BioC JSON.

        Args:
            indent: level of indentation

        Returns:
            abbreviations as BioC JSON
        """
        return json.dumps(self.abbreviations, ensure_ascii=False, indent=indent)

    def to_json(self, indent: int = 2) -> str:
        """Get the currently loaded AC object as a dict.

        Args:
            indent: Level of indentation.

        Returns:
            AC object as a JSON string
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_dict(self) -> dict[str, Any]:
        """Get the currently loaded AC object as a dict.

        Returns:
            AC object as a dict
        """
        return {
            "main_text": self.main_text,
            "abbreviations": self.abbreviations,
            "tables": self.tables,
        }
