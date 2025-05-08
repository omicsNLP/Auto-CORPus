"""This module provides a custom JSON encoder for BioCTableCollection objects."""

import json

from ..json import BioCJSONEncoder
from .cell import BioCTableCell
from .collection import BioCTableCollection
from .document import BioCTableDocument
from .passage import BioCTablePassage


class BioCTableJSONEncoder(BioCJSONEncoder):
    """Custom JSON encoder for objects with a `to_dict` method.

    This encoder extends the BioCJsonEncoder to handle objects that implement
    a `to_dict` method, converting them to a dictionary representation for JSON serialization.
    """

    def default(self, o):
        """Convert an object to a JSON-serializable dictionary.

        Parameters:
            o : object
                The object to serialize.

        Returns:
            dict
                A dictionary representation of the object if it is serializable.
        """
        match o:
            case BioCTableCell():
                return {
                    "cell_id": o.cell_id,
                    "cell_text": o.cell_text,
                }
            case BioCTablePassage():
                return {
                    "offset": o.offset,
                    "infons": o.infons,
                    "text": o.text,
                    "column_headings": [self.default(c) for c in o.column_headings],
                    "data_section": [
                        {
                            "table_section_title_1": section.get(
                                "table_section_title_1", ""
                            ),
                            "data_rows": [
                                [self.default(cell) for cell in row]
                                for row in section.get("data_rows", [])
                            ],
                        }
                        for section in o.data_section
                    ],
                    "annotations": [self.default(a) for a in o.annotations],
                    "relations": [self.default(r) for r in o.relations],
                }
            case BioCTableDocument():
                return {
                    "id": o.id,
                    "inputfile": o.inputfile,
                    "infons": o.infons,
                    "passages": [self.default(p) for p in o.passages],
                    "annotations": [self.default(a) for a in o.annotations],
                    "relations": [self.default(r) for r in o.relations],
                }
            case BioCTableCollection():
                return {
                    "source": o.source,
                    "date": o.date,
                    "key": o.key,
                    "version": o.version,
                    "infons": o.infons,
                    "documents": [self.default(d) for d in o.documents],
                }
            case _:
                # Let the base class default method raise the TypeError
                return super().default(o)


class BioCTableJSON:
    """Utility class for serializing BioCTableCollection objects to JSON."""

    @staticmethod
    def dump(obj, fp, **kwargs):
        """Serialize a BioCTableCollection object to a JSON file-like object.

        Parameters:
            obj : object
                The object to serialize.
            fp : file-like object
                The file-like object to write the JSON data to.
            **kwargs : dict
                Additional keyword arguments to pass to `json.dump`.
        """
        return json.dump(obj, fp, cls=BioCTableJSONEncoder, **kwargs)

    @staticmethod
    def dumps(obj, **kwargs):
        """Serialize a BioCTableCollection object to a JSON-formatted string.

        Parameters:
            obj : object
                The object to serialize.
            **kwargs : dict
                Additional keyword arguments to pass to `json.dumps`.

        Returns:
            str
                A JSON-formatted string representation of the object.
        """
        return json.dumps(obj, cls=BioCTableJSONEncoder, **kwargs)
