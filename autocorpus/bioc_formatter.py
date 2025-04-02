"""Top-level BioC collection builder script."""

import json
from datetime import datetime
from typing import Any

from .bioc_documents import BiocDocument


def get_formatted_bioc_collection(
    input_vals: object, json_format=False
) -> dict[str, Any] | str:
    """Constructs a BioC collection from input document-level data.

    Args:
        input_vals (object): Input document-level data.
        json_format (bool): If True, returns the collection as a JSON string.

    Returns:
        (dict | str): BioC collection
    """
    bioc_collection = {
        "source": "Auto-CORPus (full-text)",
        "date": f"{datetime.today().strftime('%Y%m%d')}",
        "key": "autocorpus_fulltext.key",
        "infons": {},
        "documents": [BiocDocument(input_vals).as_dict()],
    }

    if json_format:
        return json.dumps(bioc_collection, indent=2, ensure_ascii=False)
    return bioc_collection
