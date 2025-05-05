"""This module provides functionality for converting text extracted from various file types into a BioC format."""

import datetime
import re
from pathlib import Path
from typing import Any

import pandas as pd
from bioc import BioCAnnotation, BioCCollection, BioCDocument, BioCPassage, biocjson
from pandas import DataFrame

from autocorpus.utils import replace_unicode

from .bioctable import (
    BioCTableCell,
    BioCTableCollection,
    BioCTableDocument,
    BioCTableJSONEncoder,
    BioCTablePassage,
)


def extract_table_from_pdf_text(text):
    """Extracts tables from PDF text and returns the remaining text and tables.

    Args:
        text (str): The input text extracted from a PDF file.

    Returns:
        tuple: A tuple containing the remaining text (str) and a list of tables (list of DataFrames).
    """
    # Split the text into lines
    lines = [x for x in text.splitlines() if x]
    text_output = lines

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
        text_output.remove(line)

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
    text_output = "\n\n".join(text_output)
    return text_output, tables_output


class BioCTableConverter:
    """Converts tables from nested lists into a BioC table object."""

    def __init__(self, table_data: list[DataFrame], input_file: str):
        """Initialize a BioCTable object.

        Args:
            table_id (int): The unique identifier for the table.
            table_data (pd.DataFrame): The data of the table as a Pandas DataFrame.
            input_file (str): The source of the text content.
        """
        self.input_file = input_file
        self.current_table_id = 1
        self.textsource = "Auto-CORPus (supplementary)"
        self.infons: dict[str, Any] = {}
        self.documents: list[BioCTableDocument] = []
        self.annotations: list[dict[str, Any]] = []
        self.passages: list[BioCTablePassage] = []
        self.__build_tables(table_data)
        self.__structure_bioc()

    def __structure_bioc(self):
        # Finalize the BioC structure
        self.bioc = BioCTableCollection()
        self.bioc.source = "Auto-CORPus (supplementary)"
        self.bioc.date = datetime.date.today().strftime("%Y%m%d")
        self.bioc.key = "autocorpus_supplementary.key"
        self.bioc.infons = {}
        self.bioc.documents = self.documents

    def __build_tables(self, table_data: list[DataFrame]):
        """Builds a table passage based on the provided table_data and adds it to the passages list.

        Args:
            table_data: A pandas DataFrame containing the data for the table.

        Returns:
            None
        """
        for table_idx, table_dataframe in enumerate(table_data):
            passages: list[BioCTablePassage] = []
            # Create a title passage
            # title_passage: BioCTablePassage = BioCTablePassage()
            # title_passage.offset = 0
            # title_passage.infons = {
            #     "section_title_1": "table_title",
            #     "iao_name_1": "document title",
            #     "iao_id_1": "IAO:0000305",
            # }
            # passages.append(title_passage)
            # Create a caption passage
            # caption_passage: BioCTablePassage = BioCTablePassage()
            # caption_passage.offset = 0
            # caption_passage.infons = {
            #     "section_title_1": "table_caption",
            #     "iao_name_1": "caption",
            #     "iao_id_1": "IAO:0000304",
            # }
            # passages.append(caption_passage)
            # Create a passage for table content
            passage: BioCTablePassage = BioCTablePassage()
            passage.offset = 0
            passage.infons = {
                "section_title_1": "table_content",
                "iao_name_1": "table",
                "iao_id_1": "IAO:0000306",
            }
            # Populate column headings
            for i, text in enumerate(table_dataframe.columns.values):
                cell_id: str = str(table_idx) + f".1.{i + 1}"
                cell_text: str = replace_unicode(text)
                # use new cell object
                new_cell: BioCTableCell = BioCTableCell(
                    cell_id=cell_id, cell_text=cell_text
                )
                passage.column_headings.append(new_cell)
            # generate a new data section
            passage.data_section = [
                {
                    "table_section_title_1": "table_data",
                    "data_rows": [],
                }
            ]
            # Populate table rows with cell data
            for row_idx, row in enumerate(table_dataframe.values):
                new_row: list[BioCTableCell] = []
                for cell_idx, cell in enumerate(row):
                    data_cell_id: str = f"{table_idx}.{row_idx + 2}.{cell_idx + 1}"
                    data_cell_text: str = f"{replace_unicode(cell)}"
                    new_data_cell: BioCTableCell = BioCTableCell(
                        cell_id=data_cell_id, cell_text=data_cell_text
                    )
                    new_row.append(new_data_cell)
                passage.data_section[0]["data_rows"].append(new_row)
            # Add the table passage to the passages list
            passages.append(passage)
            temp_doc = BioCTableDocument()
            temp_doc.passages = passages
            temp_doc.inputfile = self.input_file
            temp_doc.id = f"{self.current_table_id}"
            self.documents.append(temp_doc)
            self.current_table_id += 1

    def output_tables_json(self, filename: Path) -> None:
        """Outputs the BioC data to a JSON file.

        Args:
            bioc (dict): The BioC data to be written to the file.
            filename (str): The name of the input file.
        """
        out_filename = str(filename).replace(".pdf", ".pdf_tables.json")
        with open(out_filename, "w", encoding="utf-8") as f:
            BioCTableJSONEncoder.dump(self.bioc, f, indent=4)


class BioCTextConverter:
    """Converts text into BioC format by identifying passages and annotations.

    Attributes:
        infons (dict): Metadata information for the text.
        passages (list): A list of passage objects identified from the text.
        annotations (list): A list of BioCAnnotation objects for the text.
    """

    def __init__(self, text: str, file_type_source: str, input_file: str):
        """Initialize the BioCTextConverter with text and its source type.

        Args:
            text (str): The text content to be converted.
            file_type_source (str): The source type of the text (e.g., 'word' or 'pdf').
        """
        self.input_file = input_file
        self.infons: dict[str, Any] = {}
        if file_type_source == "word":
            self.passages = self.__identify_word_passages(text)
        elif file_type_source == "pdf":
            self.passages = self.__identify_pdf_passages(text)
        self.annotations: list[BioCAnnotation] = []
        self.__structure_bioc()

    def __structure_bioc(self):
        # Finalize the BioC structure
        self.bioc = BioCCollection()
        self.bioc.source = "Auto-CORPus (supplementary)"
        self.bioc.date = datetime.date.today().strftime("%Y%m%d")
        self.bioc.key = "autocorpus_supplementary.key"
        self.bioc.infons = {}
        self.bioc.documents = []
        temp_doc = BioCDocument()
        temp_doc.passages = self.passages
        temp_doc.annotations = self.annotations
        temp_doc.infons = self.infons
        temp_doc.inputfile = self.input_file
        self.bioc.documents.append(temp_doc)

    @staticmethod
    def __identify_passages(text):
        """Identifies passages within the given text and creates passage objects.

        Args:
            text (list): The text to be processed, represented as a list of lines.

        Returns:
            list: A list of passage objects. Each passage object is a dictionary containing the following keys:
                  - "offset": The offset of the passage in the original text.
                  - "infons": A dictionary of information associated with the passage, including:
                      - "iao_name_1": The name or type of the passage.
                      - "iao_id_1": The unique identifier associated with the passage.
                  - "text": The content of the passage.
                  - "sentences": An empty list of sentences (to be populated later if needed).
                  - "annotations": An empty list of annotations (to be populated later if needed).
                  - "relations": An empty list of relations (to be populated later if needed).
        """
        offset = 0
        passages = []
        if text is None:
            return passages
        if type(text) is str:
            text = text.split("\n\n")
        else:
            text = [x.split("\n") for x in text]
            temp = []
            for i in text:
                for t in i:
                    temp.append(t)
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

    @staticmethod
    def __identify_pdf_passages(text):
        """Identifies passages within the given text and creates passage objects.

        Args:
            text (tuple): The text to be processed and a boolean which is True for header text.

        Returns:
            list: A list of passage objects. Each passage object is a dictionary containing the following keys:
                  - "offset": The offset of the passage in the original text.
                  - "infons": A dictionary of information associated with the passage, including:
                      - "iao_name_1": The name or type of the passage.
                      - "iao_id_1": The unique identifier associated with the passage.
                  - "text": The content of the passage.
                  - "sentences": An empty list of sentences (to be populated later if needed).
                  - "annotations": An empty list of annotations (to be populated later if needed).
                  - "relations": An empty list of relations (to be populated later if needed).

        Example:
            text = [
                "Introduction",
                "This is the first paragraph.",
                "Conclusion"
            ]
            passages = __identify_passages(text)
        """
        offset = 0
        passages = []
        if text is None:
            return passages
        if type(text) is str:
            text = text.split("\n\n")
        else:
            text = [x.split("\n") for x in text]
            temp = []
            for i in text:
                for t in i:
                    temp.append(t)
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

    @staticmethod
    def __identify_word_passages(text):
        """Identifies passages within the given text and creates passage objects.

        Args:
            text (tuple): The text to be processed and a boolean which is True for header text.

        Returns:
            list: A list of passage objects. Each passage object is a dictionary containing the following keys:
                  - "offset": The offset of the passage in the original text.
                  - "infons": A dictionary of information associated with the passage, including:
                      - "iao_name_1": The name or type of the passage.
                      - "iao_id_1": The unique identifier associated with the passage.
                  - "text": The content of the passage.
                  - "sentences": An empty list of sentences (to be populated later if needed).
                  - "annotations": An empty list of annotations (to be populated later if needed).
                  - "relations": An empty list of relations (to be populated later if needed).

        Example:
            text = [
                "Introduction",
                "This is the first paragraph.",
                "Conclusion"
            ]
            passages = __identify_passages(text)
        """
        offset = 0
        passages = []
        # Iterate through each line in the text
        line, is_header = text
        line = line.replace("\n", "")
        iao_name = ""
        iao_id = ""

        # Determine the type of the line and assign appropriate information
        if line.isupper() or is_header:
            iao_name = "document title"
            iao_id = "IAO:0000305"
        else:
            iao_name = "supplementary material section"
            iao_id = "IAO:0000326"
        # Create a passage object and add it to the passages list
        passage = BioCPassage()
        passage.offset = offset
        passage.infons = {"iao_name_1": iao_name, "iao_id_1": iao_id}
        passage.text = line
        # Add the passage to the list
        passages.append(passage)
        offset += len(line)
        return passages

    def output_bioc_json(self, filename: Path) -> None:
        """Outputs the BioC data to a JSON file.

        Args:
            bioc (dict): The BioC data to be written to the file.
            filename (str): The name of the input file.
        """
        out_filename = str(filename).replace(".pdf", ".pdf_bioc.json")
        with open(out_filename, "w", encoding="utf-8") as f:
            biocjson.dump(self.bioc, f, indent=4)
