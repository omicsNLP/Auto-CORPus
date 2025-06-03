"""This module provides a custom JSON encoder for BioCCollection objects.

It includes:
- BioCJSONEncoder: A subclass of JSONEncoder to handle BioC objects with a `to_dict`-like structure.
- dump: Function to serialize BioCCollection to a JSON file-like object.
- dumps: Function to serialize BioCCollection to a JSON-formatted string.
"""

import json
from typing import Any

from .collection import BioCCollection


class BioCJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for BioC-related objects."""

    def default(self, o: Any) -> Any:
        """Return a serializable object for JSON encoding, using to_dict if available."""
        if hasattr(o, "to_dict") and callable(o.to_dict):
            return o.to_dict()
        if o is None:
            return None
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
