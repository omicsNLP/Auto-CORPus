"""This module provides a custom JSON encoder for BioCCollection objects.

It includes:
- BioCJSONEncoder: A subclass of JSONEncoder to handle BioC objects with a `to_dict`-like structure.
- dump: Function to serialize BioCCollection to a JSON file-like object.
- dumps: Function to serialize BioCCollection to a JSON-formatted string.
"""

import json
from typing import Any

from .annotation import BioCAnnotation
from .collection import BioCCollection
from .document import BioCDocument
from .location import BioCLocation
from .node import BioCNode
from .passage import BioCPassage
from .relation import BioCRelation
from .sentence import BioCSentence


class BioCJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for BioC-related objects."""

    def default(self, o: Any) -> Any:
        """Override the default method to handle BioC-related objects."""
        match o:
            case BioCLocation():
                return {
                    "offset": o.offset,
                    "length": o.length,
                }

            case BioCNode():
                return {
                    "refid": o.refid,
                    "role": o.role,
                }
            case BioCSentence():
                return {
                    "offset": o.offset,
                    "infons": o.infons,
                    "text": o.text,
                    "annotations": [self.default(a) for a in o.annotations],
                    "relations": [self.default(r) for r in o.relations],
                }
            case BioCPassage():
                return {
                    "offset": o.offset,
                    "infons": o.infons,
                    "text": o.text,
                    "annotations": [self.default(a) for a in o.annotations],
                    "relations": [self.default(r) for r in o.relations],
                }
            case BioCDocument():
                return {
                    "id": o.id,
                    "infons": o.infons,
                    "inputfile": o.inputfile,
                    "passages": [self.default(p) for p in o.passages],
                    "annotations": [self.default(a) for a in o.annotations],
                    "relations": [self.default(r) for r in o.relations],
                }
            case BioCAnnotation():
                return {
                    "id": o.id,
                    "infons": o.infons,
                    "text": o.text,
                    "locations": [self.default(l) for l in o.locations],
                }
            case BioCRelation():
                return {
                    "id": o.id,
                    "infons": o.infons,
                    "nodes": [self.default(n) for n in o.nodes],
                }
            case BioCCollection():
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


class BioCJSON:
    """JSON serialization for BioC objects."""

    @staticmethod
    def dump(obj: BioCCollection, fp, **kwargs) -> None:
        """Serialize a BioCCollection object to a JSON file-like object."""
        return json.dump(obj, fp, cls=BioCJSONEncoder, **kwargs)

    @staticmethod
    def dumps(obj: BioCCollection, **kwargs) -> str:
        """Serialize a BioCCollection object to a JSON-formatted string."""
        return json.dumps(obj, cls=BioCJSONEncoder, **kwargs)

    @staticmethod
    def loads(json_str: str) -> BioCCollection:
        """Deserialize a JSON-formatted string to a BioCCollection object."""
        data = json.loads(json_str)
        return BioCCollection.from_json(data)
