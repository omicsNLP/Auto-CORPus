"""This module provides a custom JSON encoder for BioCTableCollection objects.

It includes:
- BioCTableJSONEncoder: A subclass of BioCJsonEncoder to handle objects with a `to_dict` method.
- dump: Function to serialize BioCTableCollection to a JSON file-like object.
- dumps: Function to serialize BioCTableCollection to a JSON-formatted string.
"""

import json

from bioc.biocjson import BioCJsonEncoder


class BioCTableJSONEncoder(BioCJsonEncoder):
    """Custom JSON encoder for objects with a `to_dict` method.

    This encoder extends the BioCJsonEncoder to handle objects that implement
    a `to_dict` method, converting them to a dictionary representation for JSON serialization.
    """

    def default(self, o):
        """Convert an object to a dictionary if it has a `to_dict` method.

        Parameters:
            o : object
                The object to be serialized.

        Returns:
            dict or object
                A dictionary representation of the object if it has a `to_dict` method,
                otherwise the result of the superclass's `default` method.
        """
        if hasattr(o, "to_dict"):
            return o.to_dict()
        return super().default(o)


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
