"""Top-level BioC collection builder script."""

from datetime import datetime
from typing import Any

from .bioc_documents import BiocDocument


def get_formatted_bioc_collection(input_vals: object) -> dict[str, Any] | str:
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
    return bioc_collection
