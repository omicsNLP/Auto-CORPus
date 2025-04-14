"""This module provides functionality to extract and convert PDF content into BioC format.

It includes classes and functions for processing text, tables, and other components
extracted from PDFs, and converting them into structured BioC objects.
"""

import datetime
from pathlib import Path
from typing import Any

from bioc import BioCCollection, BioCDocument, BioCPassage
from pandas import DataFrame


def get_pdf_passages(text: list[str] | str) -> list[BioCPassage] | list[str]:
    """Identifies passages within the given text and creates passage objects.

    Args:
        text (list): The text to be processed, represented as a list of lines.

    Returns:
        list: A list of BioCPassage objects.
    """
    offset = 0
    passages: list[BioCPassage] = []
    if not text:
        return passages
    if isinstance(text, str):
        text = text.split("\n\n")
    text = [x for x in text if x]
    # Iterate through each line in the text
    for line in text:
        # Determine the type of the line and assign appropriate information
        iao_name = "supplementary material section"
        iao_id = "IAO:0000326"
        # Create a passage object and add it to the passages list
        passage = BioCPassage()
        passage.offset = offset
        passage.infons = {"iao_name_1": iao_name, "iao_id_1": iao_id}
        passage.text = line
        passages.append(passage)
        offset += len(line)
    return passages


def get_text_bioc(parsed_texts: list[str], filename: str):
    """Convert parsed texts into BioC format.

    Args:
        parsed_texts (list): A list of parsed text segments to be converted.
        filename (str): The name of the source file.
        textsource (str): The source of the text, default is "Auto-CORPus".

    Returns:
        BioCCollection: A BioCCollection object representing the converted text in BioC format.
    """
    passages = [
        p
        for sublist in [
            get_pdf_passages(replace_unicode(x)).__dict__["passages"]
            for x in parsed_texts
        ]
        for p in sublist
    ]
    offset = 0
    for p in passages:
        p["offset"] = offset
        offset += len(p["text"])
    # Create a BioC XML structure dictionary
    bioc = BioCCollection()
    bioc.source = "Auto-CORPus (supplementary)"
    bioc.date = datetime.date.today().strftime("%Y%m%d")
    bioc.key = "autocorpus_supplementary.key"
    bioc.documents = []
    new_doc = BioCDocument()
    new_doc.id = "1"
    new_doc.infons = {
        "inputfile": Path(filename).name,
        "textsource": "Auto-CORPus (supplementary)",
    }
    new_doc.passages = passages
    return bioc


def convert_pdf_result(tables, text, input_file):
    """Convert the result of processing a PDF into a BioC format.

    Args:
        tables (DataFrame): The extracted tables from the PDF.
        text (list): The extracted text from the PDF.
        input_file (str): The path of the input PDF file.

    Returns:
        tuple: A tuple containing the converted BioC text and tables.
            - bioc_text (str): The converted text in BioC format.
            - bioc_tables (str): The converted tables in BioC format.

    The function takes three parameters: `tables`, `text`, and `input_file`.

    It calls the `get_tables_bioc` function to convert the extracted tables (`tables`) into BioC format.
    It passes `tables` and `input_file` as arguments to `get_tables_bioc`.

    It also calls the `get_text_bioc` function to convert the extracted text (`text`) into BioC format.

    Finally, the function returns a tuple containing the converted BioC text and tables as `bioc_text` and `bioc_tables`, respectively.
    """
    bioc_text, bioc_tables = None, None
    if text:
        bioc_text = get_text_bioc(text, input_file)
    if tables:
        bioc_tables = get_tables_bioc(tables, input_file)
    return bioc_text, bioc_tables
