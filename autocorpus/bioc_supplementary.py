"""This module provides functionality for converting text extracted from various file types into a BioC format."""

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import regex
from pandas import DataFrame

from .ac_bioc import (
    BioCCollection,
    BioCDocument,
    BioCJSON,
    BioCPassage,
)
from .ac_bioc.bioctable import (
    BioCTableCell,
    BioCTableCollection,
    BioCTableDocument,
    BioCTableJSON,
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


def replace_unicode(text):
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
    if not text:
        return None
    if isinstance(text, list):
        clean_texts = []
        for t in text:
            if t:
                clean_texts.append(
                    t.replace("\u00a0", " ")
                    .replace("\u00ad", "-")
                    .replace("\u2010", "-")
                    .replace("\u00d7", "x")
                )
        return clean_texts
    else:
        clean_text = (
            text.replace("\u00a0", " ")
            .replace("\u00ad", "-")
            .replace("\u2010", "-")
            .replace("\u00d7", "x")
        )
        return clean_text


@dataclass
class BioCTableConverter:
    """Converts tables from nested lists into a BioC table object."""

    table_data: list["DataFrame"]
    input_file: str

    current_table_id: int = 1
    textsource: str = "Auto-CORPus (supplementary)"
    infons: dict[str, Any] = field(default_factory=dict)
    documents: list["BioCTableDocument"] = field(default_factory=list)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    passages: list["BioCTablePassage"] = field(default_factory=list)
    bioc: Any = field(init=False)

    def __post_init__(self):
        """Initializes the object after its creation by building tables and structuring the BioC object."""
        self.__build_tables(self.table_data)
        self.__structure_bioc()

    def __structure_bioc(self):
        self.bioc = BioCTableCollection()
        self.bioc.source = self.textsource
        self.bioc.date = datetime.date.today().strftime("%Y%m%d")
        self.bioc.key = "autocorpus_supplementary.key"
        self.bioc.infons = {}
        self.bioc.documents = self.documents

    def __build_tables(self, table_data: list[DataFrame]):
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
            temp_doc = BioCTableDocument(id=str(self.current_table_id))
            temp_doc.passages = passages
            temp_doc.inputfile = self.input_file
            self.documents.append(temp_doc)
            self.current_table_id += 1

    def output_tables_json(self, filename: Path) -> None:
        """Outputs the BioC table collection as a JSON file.

        Args:
            filename (Path): The path to the input file, which will be used to generate the output JSON filename.
        """
        out_filename = str(filename).replace(".pdf", ".pdf_tables.json")
        with open(out_filename, "w", encoding="utf-8") as f:
            BioCTableJSON.dump(self.bioc, f, indent=4)


@dataclass
class BioCTextConverter:
    """Converts text content into a BioC format for supplementary material processing."""

    text: str
    file_type_source: str
    input_file: str

    document_id: int = 1
    infons: dict[str, Any] = field(default_factory=dict)
    passages: list[Any] = field(init=False)
    annotations: list[Any] = field(default_factory=list)
    bioc: Any = field(init=False)

    def __post_init__(self):
        """Initializes passages based on the file type source and structures the BioC object."""
        if self.file_type_source == "word":
            self.passages = self.__identify_word_passages(self.text)
        elif self.file_type_source == "pdf":
            self.passages = self.__identify_pdf_passages(self.text)
        else:
            self.passages = []
        self.__structure_bioc()

    def __structure_bioc(self):
        self.bioc = BioCCollection()
        self.bioc.source = "Auto-CORPus (supplementary)"
        self.bioc.date = datetime.date.today().strftime("%Y%m%d")
        self.bioc.key = "autocorpus_supplementary.key"
        self.bioc.infons = {}
        self.bioc.documents = []
        temp_doc = BioCDocument(id=str(self.document_id))
        temp_doc.passages = self.passages
        temp_doc.annotations = self.annotations
        temp_doc.infons = self.infons
        temp_doc.inputfile = self.input_file
        self.document_id += 1
        self.bioc.documents.append(temp_doc)

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
    def __identify_pdf_passages(text):
        return BioCTextConverter.__identify_passages(text)

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

    def output_bioc_json(self, filename: Path) -> None:
        """Outputs the BioC collection as a JSON file.

        Args:
            filename (Path): The path to the input file, which will be used to generate the output JSON filename.
        """
        out_filename = str(filename).replace(".pdf", ".pdf_bioc.json")
        with open(out_filename, "w", encoding="utf-8") as f:
            BioCJSON.dump(self.bioc, f, indent=4)
