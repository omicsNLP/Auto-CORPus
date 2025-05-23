"""Top-level BioC collection builder script."""

from datetime import datetime
from typing import Any

from autocorpus.bioc_documents import get_formatted_bioc_document


def get_formatted_bioc_collection(input_vals: object) -> dict[str, Any]:
    """Constructs a BioC collection from input document-level data.

    Args:
        input_vals (object): Input document-level data.

    Returns:
        (dict): BioC collection
    """
    bioc_collection = {
        "source": "Auto-CORPus (full-text)",
        "date": datetime.today().strftime("%Y%m%d"),
        "key": "autocorpus_fulltext.key",
        "infons": {},
        "documents": [get_formatted_bioc_document(input_vals)],
    }
    return bioc_collection
