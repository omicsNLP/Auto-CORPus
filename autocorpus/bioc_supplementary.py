"""This module provides functionality for converting text extracted from various file types into a BioC format."""

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
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


def extract_table_from_pdf_text(text: str) -> tuple[str, list[DataFrame]]:
    """Extracts tables from PDF text and returns the remaining text and tables.

    Args:
        text (str): The input text extracted from a PDF file.

    Returns:
        tuple: A tuple containing the remaining text (str) and a list of tables (list of DataFrames).
    """
    # Split the text into lines
    lines = [x for x in text.splitlines() if x]
    temp_text_output = lines

    # store extracted tables
    tables = []
    # Identify where the table starts and ends by looking for lines containing pipes
    table_lines = []
    # keep unmodified lines used in tables. These must be removed from the original text
    lines_to_remove = []
    inside_table = False
    for line in lines:
        if "|" in line:
            inside_table = True
            table_lines.append(line)
            lines_to_remove.append(line)
        elif (
            inside_table
        ):  # End of table if there's a blank line after lines with pipes
            inside_table = False
            tables.append(table_lines)
            table_lines = []
            continue

    for line in lines_to_remove:
        temp_text_output.remove(line)

    tables_output = []
    # Remove lines that are just dashes (table separators)
    for table in tables:
        table = [line for line in table if not re.match(r"^\s*-+\s*$", line)]

        # Extract rows from the identified table lines
        rows = []
        for line in table:
            # Match only lines that look like table rows (contain pipes)
            if re.search(r"\|", line):
                # Split the line into cells using the pipe delimiter and strip whitespace
                cells = [
                    cell.strip()
                    for cell in line.split("|")
                    if not all(x in "|-" for x in cell)
                ]
                if cells:
                    rows.append(cells)

        # Determine the maximum number of columns in the table
        num_columns = max(len(row) for row in rows)

        # Pad rows with missing cells to ensure they all have the same length
        for row in rows:
            while len(row) < num_columns:
                row.append("")

        # Create a DataFrame from the rows
        df = pd.DataFrame(rows[1:], columns=rows[0])
        tables_output.append(df)
    text_output = "\n\n".join(temp_text_output)
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
            passages: list[BioCTablePassage] = []
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
        out_filename = str(filename).replace(".pdf", ".pdf_bioc.json")
        with open(out_filename, "w", encoding="utf-8") as f:
            BioCJSON.dump(self.bioc, f, indent=4)
