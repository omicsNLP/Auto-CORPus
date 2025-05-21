"""Top-level BioC collection builder script."""

from datetime import datetime
from typing import Any

from autocorpus.bioc_documents import get_formatted_bioc_document


def get_formatted_bioc_collection(
    main_text: dict[str, Any],
    file_path: str,
) -> dict[str, Any]:  # TODO: Change return type to ac_bioc.BioCCollection
    """Constructs a BioC collection from input document-level data.

    Args:
        main_text: Input document-level data.
        file_path: Path to the input file.

    Returns:
        BioC collection
    """
    bioc_collection = {
        "source": "Auto-CORPus (full-text)",
        "date": datetime.today().strftime("%Y%m%d"),
        "key": "autocorpus_fulltext.key",
        "infons": {},
        "documents": [get_formatted_bioc_document(main_text, file_path)],
    }
    return bioc_collection
