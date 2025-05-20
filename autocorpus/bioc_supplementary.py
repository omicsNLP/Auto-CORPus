"""This module provides functionality for converting text extracted from various file types into a BioC format."""

import datetime
from typing import TypeVar

import pandas as pd
import regex
from pandas import DataFrame

from .ac_bioc import (
    BioCCollection,
    BioCDocument,
    BioCPassage,
)
from .ac_bioc.bioctable import (
    BioCTableCell,
    BioCTableCollection,
    BioCTableDocument,
    BioCTablePassage,
)


def _split_text_and_tables(text: str) -> tuple[list[str], list[list[str]]]:
    """Splits PDF text into main text lines and raw table lines."""
    lines = [x for x in text.splitlines() if x]
    tables = []
    table_lines = []
    main_text_lines = []
    inside_table = False

    for line in lines:
        if "|" in line:
            inside_table = True
            table_lines.append(line)
        elif inside_table:
            inside_table = False
            tables.append(table_lines)
            main_text_lines.append(line)
            table_lines = []
            continue
        else:
            main_text_lines.append(line)

    return main_text_lines, tables


def _parse_tables(raw_tables: list[list[str]]) -> list[DataFrame]:
    """Converts raw table text lines into DataFrames."""
    parsed_tables = []
    for table in raw_tables:
        # Remove lines that are just dashes
        table = [line for line in table if not regex.match(r"^\s*[\p{Pd}]+\s*$", line)]

        rows = []
        for line in table:
            if regex.search(r"\|", line):
                cells = [
                    cell.strip()
                    for cell in line.split("|")
                    if not all(x in "|-" for x in cell)
                ]
                if cells:
                    rows.append(cells)

        if not rows:
            continue

        num_columns = max(len(row) for row in rows)
        for row in rows:
            while len(row) < num_columns:
                row.append("")

        df = pd.DataFrame(rows[1:], columns=rows[0])
        parsed_tables.append(df)

    return parsed_tables


def extract_table_from_pdf_text(text: str) -> tuple[str, list[DataFrame]]:
    """Extracts tables from PDF text and returns the remaining text and parsed tables."""
    main_text_lines, raw_tables = _split_text_and_tables(text)
    tables_output = _parse_tables(raw_tables)
    text_output = "\n\n".join(main_text_lines)
    return text_output, tables_output


def string_replace_unicode(text: str) -> str:
    """Replaces specific Unicode characters with their corresponding replacements in the given text."""
    return (
        text.replace("\u00a0", " ")
        .replace("\u00ad", "-")
        .replace("\u2010", "-")
        .replace("\u00d7", "x")
    )


T = TypeVar("T", str, list[str])


def replace_unicode(text: T) -> T:
    """Replaces specific Unicode characters with their corresponding replacements in the given text.

    Args:
        text (str or list): The input text or list of texts to process.

    Returns:
        str or list: The processed text or list of processed texts.

    If the input `text` is empty or None, the function returns None.

    If the input `text` is a list, it iterates over each element of the list and replaces the following Unicode characters:
        - '\u00a0': Replaced with a space ' '
        - '\u00ad': Replaced with a hyphen '-'
        - '\u2010': Replaced with a hyphen '-'
        - '\u00d7': Replaced with a lowercase 'x'

    If the input `text` is not a list, it directly replaces the Unicode characters mentioned above.

    Returns the processed text or list of processed texts.
    """
    if isinstance(text, list):
        clean_texts = []
        for t in text:
            if t:
                clean_texts.append(string_replace_unicode(t))
        return clean_texts
    else:
        clean_text = string_replace_unicode(text)
        return clean_text


class BioCTableConverter:
    """Converts tables from nested lists into a BioC table object."""

    @staticmethod
    def build_bioc(table_data: list[DataFrame], input_file: str) -> BioCTableCollection:
        """Builds a BioCTableCollection object from the provided table data and input file.

        Args:
            table_data (list[DataFrame]): List of pandas DataFrames representing tables.
            input_file (str): The path to the input file.
        """
        bioc = BioCTableCollection()
        bioc.source = "Auto-CORPus (supplementary)"
        bioc.date = datetime.date.today().strftime("%Y%m%d")
        bioc.key = "autocorpus_supplementary.key"
        bioc.infons = {}
        bioc.documents = BioCTableConverter.__build_tables(table_data, input_file)
        return bioc

    @staticmethod
    def __build_tables(
        table_data: list[DataFrame], input_file: str
    ) -> list[BioCDocument]:
        current_table_id = 1
        documents: list[BioCDocument] = []
        for table_idx, table_dataframe in enumerate(table_data):
            passages: list[BioCPassage] = []
            passage: BioCTablePassage = BioCTablePassage()
            passage.offset = 0
            passage.infons = {
                "section_title_1": "table_content",
                "iao_name_1": "table",
                "iao_id_1": "IAO:0000306",
            }

            for i, text in enumerate(table_dataframe.columns.values):
                cell_id: str = f"{table_idx}.1.{i + 1}"
                cell_text: str = replace_unicode(text)
                new_cell = BioCTableCell(cell_id=cell_id, cell_text=cell_text)
                passage.column_headings.append(new_cell)

            passage.data_section = [
                {
                    "table_section_title_1": "table_data",
                    "data_rows": [],
                }
            ]

            for row_idx, row in enumerate(table_dataframe.values):
                new_row: list[BioCTableCell] = []
                for cell_idx, cell in enumerate(row):
                    data_cell_id = f"{table_idx}.{row_idx + 2}.{cell_idx + 1}"
                    cleaned_text = replace_unicode(cell)
                    data_cell_text = cleaned_text if cleaned_text else ""
                    new_data_cell = BioCTableCell(
                        cell_id=data_cell_id, cell_text=data_cell_text
                    )
                    new_row.append(new_data_cell)
                passage.data_section[0]["data_rows"].append(new_row)

            passages.append(passage)
            temp_doc = BioCTableDocument(id=str(current_table_id))
            temp_doc.passages = passages
            temp_doc.inputfile = input_file
            documents.append(temp_doc)
            current_table_id += 1
        return documents


class BioCTextConverter:
    """Converts text content into a BioC format for supplementary material processing."""
    
    @staticmethod
    def build_bioc(text: str, input_file: str, file_type: str) -> BioCCollection:
        """Builds a BioCCollection object from the provided text, input file, and file type.

        Args:
            text (str): The text content to be converted.
            input_file (str): The path to the input file.
            file_type (str): The type of the input file ('word' or 'pdf').

        Returns:
            BioCCollection: The constructed BioCCollection object.
        """
        bioc = BioCCollection()
        bioc.source = "Auto-CORPus (supplementary)"
        bioc.date = datetime.date.today().strftime("%Y%m%d")
        bioc.key = "autocorpus_supplementary.key"
        temp_doc = BioCDocument(id="1")
        if file_type == "word":
            temp_doc.passages = BioCTextConverter.__identify_word_passages(text)
        elif file_type == "pdf":
            temp_doc.passages = BioCTextConverter.__identify_passages(text)
        temp_doc.passages = BioCTextConverter.__identify_passages(text)
        temp_doc.inputfile = input_file
        bioc.documents.append(temp_doc)
        return bioc

    @staticmethod
    def __identify_passages(text):
        offset = 0
        passages = []
        if text is None:
            return passages
        if isinstance(text, str):
            text = text.split("\n\n")
        else:
            text = [x.split("\n") for x in text]
            temp = []
            for i in text:
                for t in i:
                    temp.append(t)
            text = temp
        text = [x for x in text if x]
        for line in text:
            iao_name = "supplementary material section"
            iao_id = "IAO:0000326"
            passage = BioCPassage()
            passage.offset = offset
            passage.infons = {"iao_name_1": iao_name, "iao_id_1": iao_id}
            passage.text = line
            passages.append(passage)
            offset += len(line)
        return passages

    @staticmethod
    def __identify_word_passages(text):
        offset = 0
        passages = []
        line, is_header = text
        line = line.replace("\n", "")
        if line.isupper() or is_header:
            iao_name = "document title"
            iao_id = "IAO:0000305"
        else:
            iao_name = "supplementary material section"
            iao_id = "IAO:0000326"
        passage = BioCPassage()
        passage.offset = offset
        passage.infons = {"iao_name_1": iao_name, "iao_id_1": iao_id}
        passage.text = line
        passages.append(passage)
        offset += len(line)
        return passages
