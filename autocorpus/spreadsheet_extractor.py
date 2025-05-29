from pathlib import Path

import pandas as pd
from pandas import DataFrame

from . import logger


def convert_datetime_to_string(df: DataFrame) -> DataFrame:
    """Convert all datetime objects in a DataFrame to string format.

    Args:
        df: The input DataFrame.

    Returns:
        DataFrame: A DataFrame with datetime columns converted to string.
    """
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64"]):
        df[col] = df[col].astype(str)
    return df


def extract_spreadsheet_content(filename: Path) -> list[DataFrame]:
    """Process an Excel file and extract each sheet as a separate table.

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
            df = convert_datetime_to_string(df)
            # add the dataframe to the list of tables
            tables.append(df)
    except Exception as ex:
        logger.error(msg=f"The following error was raised processing {filename}: {ex}")

    # return the list of tables
    return tables
