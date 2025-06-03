"""Top-level BioC collection builder script."""

from datetime import datetime
from pathlib import Path
from typing import Any

from .ac_bioc import BioCCollection, BioCDocument, BioCPassage


def get_formatted_bioc_collection(
    main_text: dict[str, Any],
    file_path: Path,
) -> BioCCollection:  # TODO: Change return type to ac_bioc.BioCCollection
    """Constructs a BioC collection from input document-level data.

    Args:
        main_text: Input document-level data.
        file_path: Path to the input file.

    Returns:
        BioC collection
    """
    bioc_collection = BioCCollection(
        date=datetime.today().strftime("%Y%m%d"),
        documents=[get_formatted_bioc_document(main_text, file_path)],
        source="Auto-CORPus (full-text)",
        key="autocorpus_fulltext.key",
    )
    return bioc_collection


def get_formatted_bioc_document(
    main_text: dict[str, Any],
    file_path: Path,
) -> BioCDocument:  # TODO: Change return type to ac_bioc.BioCDocument
    """Constructs the BioC document template using the provided data store.

    Args:
        main_text: Input document-level data.
        file_path: Path to the input file.

    Returns:
        BioC document complete populated with passages.
    """
    # build document passages
    seen_headings = []
    passages = [BioCPassage().from_title(main_text["title"], 0)]
    offset = 0  # offset for passage start position
    if main_text["title"] not in seen_headings:
        offset = len(main_text["title"])
        seen_headings.append(main_text["title"])
    for passage in main_text["paragraphs"]:
        passage["offset"] = offset
        passage_obj = BioCPassage().from_ac_dict(passage)
        passages.append(passage_obj)
        offset += len(passage["body"])
        if passage["subsection_heading"] not in seen_headings:
            offset += len(passage["subsection_heading"])
            seen_headings.append(passage["subsection_heading"])
        if passage["section_heading"] not in seen_headings:
            offset += len(passage["section_heading"])
            seen_headings.append(passage["section_heading"])

    return BioCDocument(
        id=file_path.name.split(".")[0], inputfile=str(file_path), passages=passages
    )
