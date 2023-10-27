import datetime
import json
import os
from os.path import join

import pandas as pd
import logging

from utils import BioCTable

accepted_extensions = [".xls", ".csv", ".xlsx"]
logging.basicConfig(filename="ExcelExtractor.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %("
                                                                               "message)s")


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
        "source": "ExcelExtractor",
        "date": str(datetime.date.today().strftime("%Y%m%d")),
        "key": "excelextractor.key",
        "infons": {},
        "documents": [BioCTable(filename, i + 1, x).__dict__ for i, x in enumerate(tables)]
    }
    return bioc


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
