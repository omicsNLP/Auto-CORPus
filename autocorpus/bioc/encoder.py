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
from .key import BioCKey
from .passage import BioCPassage
from .relation import BioCRelation
from .sentence import BioCSentence


class BioCJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for BioC-related objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, BioCSentence):
            return {
                "offset": o.offset,
                "infons": o.infons,
                "text": o.text,
                "annotations": [self.default(a) for a in o.annotations],
                "relations": [self.default(r) for r in o.relations],
            }
        if isinstance(o, BioCPassage):
            return {
                "offset": o.offset,
                "infons": o.infons,
                "text": o.text,
                "annotations": [self.default(a) for a in o.annotations],
                "relations": [self.default(r) for r in o.relations],
            }
        if isinstance(o, BioCDocument):
            return {
                "id": o.id,
                "infons": o.infons,
                "inputfile": o.inputfile,
                "passages": [self.default(p) for p in o.passages],
                "annotations": [self.default(a) for a in o.annotations],
                "relations": [self.default(r) for r in o.relations],
            }
        if isinstance(o, BioCAnnotation):
            return {
                "id": o.id,
                "infons": o.infons,
                "text": o.text,
                "locations": [self.default(l) for l in o.locations],
            }
        if isinstance(o, BioCRelation):
            return {
                "id": o.id,
                "infons": o.infons,
                "nodes": [self.default(n) for n in o.nodes],
            }
        if isinstance(o, BioCCollection):
            return {
                "source": o.source,
                "date": o.date,
                "key": o.key,
                "version": o.version,
                "infons": o.infons,
                "documents": [self.default(d) for d in o.documents],
            }

        return super().default(o)


def dump(obj: BioCCollection, fp, **kwargs) -> None:
    """Serialize a BioCCollection object to a JSON file-like object."""
    return json.dump(obj, fp, cls=BioCJSONEncoder, **kwargs)


def dumps(obj: BioCCollection, **kwargs) -> str:
    """Serialize a BioCCollection object to a JSON-formatted string."""
    return json.dumps(obj, cls=BioCJSONEncoder, **kwargs)


# Stub for future XML support
class BioCXMLEncoder:
    def default(self, o: Any) -> Any:
        pass  # Not implemented yet
