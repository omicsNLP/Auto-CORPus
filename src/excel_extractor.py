import datetime
import json
import os
from os.path import join

import pandas as pd
import logging

accepted_extensions = [".xls", ".csv", ".xlsx"]
logging.basicConfig(filename="ExcelExtractor.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %("
                                                                               "message)s")


class BioCTable:
    """
    Converts tables from nested lists into a BioC table object.
    """

    def __init__(self, table_id, table_data):
        self.id = str(table_id) + "_1"
        self.infons = {}
        self.passages = []
        self.annotations = []
        self.__build_table(table_data)

    def __build_table(self, table_data):
        """
        Builds a table passage based on the provided table_data and adds it to the passages list.

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
                "iao_id_1": "IAO:0000305"
            },
        }
        self.passages.append(title_passage)
        # Create a caption passage
        caption_passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_caption",
                "iao_name_1": "caption",
                "iao_id_1": "IAO:0000304"
            },
        }
        self.passages.append(caption_passage)
        # Create a passage for table content
        passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_content",
                "iao_name_1": "table",
                "iao_id_1": "IAO:0000306"
            },
            "column_headings": [],
            "data_section": [
                {
                    "table_section_title_1": "",
                    "data_rows": [

                    ]
                }
            ]
        }
        # Populate column headings
        for i, text in enumerate(table_data.columns.values):
            passage["column_headings"].append(
                {
                    "cell_id": self.id + F".1.{i + 1}",
                    "cell_text": replace_unicode(text)
                }
            )
        # Populate table rows with cell data
        for row_idx, row in enumerate(table_data.values):
            new_row = []
            for cell_idx, cell in enumerate(row):
                new_cell = {
                    "cell_id": F"{self.id}.{row_idx + 2}.{cell_idx + 1}",
                    "cell_text": F"{replace_unicode(cell)}"
                }
                new_row.append(new_cell)
            passage["data_section"][0]["data_rows"].append(new_row)
        # Add the table passage to the passages list
        self.passages.append(passage)


def get_tables_bioc(tables, filename):
    """
    Converts extracted tables into BioC format.

    Args:
        tables: A list of tables extracted from an Excel file.
        filename: The name of the Excel file.

    Returns:
        A BioC format representation of the extracted tables.
    """
    # Create a BioC dictionary
    bioc = {
        "source": "Auto-CORPus (supplementary)",
        "date": str(datetime.date.today().strftime("%Y%m%d")),
        "key": "autocorpus_supplementary.key",
        "infons": {},
        "documents": [BioCTable(i + 1, x).__dict__ for i, x in enumerate(tables)]
    }
    return bioc


def replace_unicode(text):
    """
    Replaces specific Unicode characters in a given text.

    Args:
        text: The input text to be processed.

    Returns:
        The processed text with the specified Unicode characters replaced.

    Examples:
        replace_unicode('\u00a0Hello\u00adWorld\u2010')  # ' Hello-World-'
        replace_unicode(['\u00a0Hello', '\u00adWorld'])  # [' Hello', 'World']
    """
    if not text:
        return None
    if type(text) == list:
        clean_texts = []
        for t in text:
            if t and type(t) == str:
                clean_texts.append(
                    t.replace('\u00a0', ' ').replace('\u00ad', '-').replace('\u2010', '-').replace('\u00d7', 'x'))
            else:
                clean_texts.append(t)
        return clean_texts
    else:
        if type(text) == str:
            clean_text = text.replace('\u00a0', ' ').replace('\u00ad', '-').replace('\u2010', '-').replace('\u00d7',
                                                                                                           'x')
        else:
            clean_text = text
        return clean_text


def process_spreadsheet(filename):
    """
    Process an Excel file and extract each sheet as a separate table.

    Args:
        filename: The path of the Excel file to be processed.

    Returns:
        A list of tables, where each table is represented as a Pandas DataFrame.

    Raises:
        Exception: If there is an error while processing the Excel file.
    """
    tables = []
    try:
        # read the Excel file into a Pandas dataframe
        xls = pd.ExcelFile(filename)

        # loop through each sheet in the Excel file
        for sheet_name in xls.sheet_names:
            # read the sheet into a Pandas dataframe
            df = pd.read_excel(filename, sheet_name=sheet_name)

            # add the dataframe to the list of tables
            tables.append(df)
    except Exception as ex:
        logging.error(msg=F"The following error was raised processing {filename}: {ex}")

    # return the list of tables
    return tables


def process_directories(input_directory):
    """
    Process files in a given directory and generate BioC format representations of Excel tables.

    Args:
        input_directory: The directory path containing the files to be processed.

    Returns:
        None

    Raises:
        OSError: If there is an error while accessing or reading files in the directory.
    """
    for parent, folders_in_parent, files_in_parent in os.walk(input_directory):
        for file in files_in_parent:
            # Check if the file has an accepted extension
            if [x for x in accepted_extensions if file.endswith(x)]:
                # Process the spreadsheet and extract tables
                tables = process_spreadsheet(join(parent, file))
                # If tables are extracted
                if tables:
                    # Create a JSON output file for the extracted tables
                    with open(F"{os.path.join(parent, 'Excel_tables.json')}", "w", encoding="utf-8") as f_out:
                        # Generate BioC format representation of the tables
                        json_output = get_tables_bioc(tables, join(parent, file))
                        json.dump(json_output, f_out, indent=4)
                    logging.info(F"Output: {os.path.join(parent, 'Excel_tables.json')}")
