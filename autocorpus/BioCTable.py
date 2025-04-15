"""This module provides functionality for converting tables into an extended BioC format.

BioCTable objects include table-specific elements such as cell IDs for annotation.
"""

import datetime
from typing import Any

from pandas import DataFrame

from autocorpus.utils import replace_unicode


class BioCTable:
    """Converts tables from nested lists into a BioC table object."""

    def __init__(self, table_id: int, table_data: DataFrame):
        """Initialize a BioCTable object.

        Args:
            table_id (int): The unique identifier for the table.
            table_data (pd.DataFrame): The data of the table as a Pandas DataFrame.
            textsource (str): The source of the text content.
        """
        self.id = str(table_id) + "_1"
        self.textsource = "Auto-CORPus (supplementary)"
        self.infons: dict[str, Any] = {}
        self.passages: list[dict[str, Any]] = []
        self.annotations: list[dict[str, Any]] = []
        self.__build_table(table_data)

    def __build_table(self, table_data: DataFrame):
        """Builds a table passage based on the provided table_data and adds it to the passages list.

        Args:
            table_data: A pandas DataFrame containing the data for the table.

        Returns:
            None
        """
        # Create a title passage
        title_passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_title",
                "iao_name_1": "document title",
                "iao_id_1": "IAO:0000305",
            },
        }
        self.passages.append(title_passage)
        # Create a caption passage
        caption_passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_caption",
                "iao_name_1": "caption",
                "iao_id_1": "IAO:0000304",
            },
        }
        self.passages.append(caption_passage)
        # Create a passage for table content
        passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_content",
                "iao_name_1": "table",
                "iao_id_1": "IAO:0000306",
            },
            "column_headings": [],
            "data_section": [{"table_section_title_1": "", "data_rows": []}],
        }
        # Populate column headings
        for i, text in enumerate(table_data.columns.values):
            passage["column_headings"].append(
                {"cell_id": self.id + f".1.{i + 1}", "cell_text": replace_unicode(text)}
            )
        # Populate table rows with cell data
        for row_idx, row in enumerate(table_data.values):
            new_row = []
            for cell_idx, cell in enumerate(row):
                new_cell = {
                    "cell_id": f"{self.id}.{row_idx + 2}.{cell_idx + 1}",
                    "cell_text": f"{replace_unicode(cell)}",
                }
                new_row.append(new_cell)
            passage["data_section"][0]["data_rows"].append(new_row)
        # Add the table passage to the passages list
        self.passages.append(passage)


def get_tables_bioc(tables: list[DataFrame]) -> dict[str, Any]:
    """Converts extracted tables into BioC format.

    Args:
        tables: A list of tables extracted from an Excel file.
        filename: The name of the Excel file.
        textsource: Source of the text content.

    Returns:
        A BioC format representation of the extracted tables.
    """
    # Create a BioC dictionary
    bioc = {
        "source": "Auto-CORPus (supplementary)",
        "date": datetime.date.today().strftime("%Y%m%d"),
        "key": "autocorpus_supplementary.key",
        "infons": {},
        "documents": [BioCTable(i + 1, x).__dict__ for i, x in enumerate(tables)],
    }
    return bioc


def convert_datetime_to_string(df: DataFrame) -> DataFrame:
    """Convert all datetime objects in a DataFrame to string format.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with datetime columns converted to string.
    """
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64"]):
        df[col] = df[col].astype(str)
    return df


def get_blank_cell_count(row: list[dict[str, str]]) -> int:
    """Counts the number of blank cells in a given row.

    Args:
        row (list): A list of dictionaries representing cells in a row.

    Returns:
        int: The number of blank cells in the row.
    """
    blank_count = 0
    for cell in row:
        if not cell["text"].strip():
            blank_count += 1
    return blank_count
