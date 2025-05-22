"""Script for handling construction of BioC documents."""

from pathlib import Path
from typing import Any

from .bioc_passage import BioCPassage


def get_formatted_bioc_document(data_store) -> dict[str, Any]:
    """Constructs the BioC document template using the provided data store.

    Args:
        data_store (Autocorpus): Input article data store.

    Returns:
        (dict): BioC document complete populated with passages.
    """
    # build document passages
    seen_headings = []
    passages = [BioCPassage.from_title(data_store.main_text["title"], 0).as_dict()]
    offset = 0  # offset for passage start position
    if data_store.main_text["title"] not in seen_headings:
        offset = len(data_store.main_text["title"])
        seen_headings.append(data_store.main_text["title"])
    for passage in data_store.main_text["paragraphs"]:
        passage_obj = BioCPassage.from_dict(passage, offset)
        passages.append(passage_obj.as_dict())
        offset += len(passage["body"])
        if passage["subsection_heading"] not in seen_headings:
            offset += len(passage["subsection_heading"])
            seen_headings.append(passage["subsection_heading"])
        if passage["section_heading"] not in seen_headings:
            offset += len(passage["section_heading"])
            seen_headings.append(passage["section_heading"])

    return {
        "id": Path(data_store.file_path).name.split(".")[0],
        "inputfile": str(data_store.file_path),
        "infons": {},
        "passages": passages,
        "annotations": [],
        "relations": [],
    }
