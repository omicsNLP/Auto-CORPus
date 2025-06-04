"""Module for extracting and converting spreadsheet content into BioC tables."""

from pathlib import Path

import pandas as pd
from pandas import DataFrame

from . import logger
from .ac_bioc.bioctable.collection import BioCTableCollection
from .bioc_supplementary import BioCTableConverter


def convert_datetime_to_string(df: DataFrame) -> DataFrame:
    """Convert all datetime objects in a DataFrame to string format.

    Args:
        df: The input DataFrame.

    Returns:
        DataFrame: A DataFrame with datetime columns converted to string.
    """
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64"]):
        df[col] = df[col].astype(str)
        df[col] = df[col].fillna("")
    return df


def extract_spreadsheet_content(filename: Path) -> BioCTableCollection | None:
    """Process an Excel file and extract each sheet as a separate table.

    Args:
        filename: The path of the Excel file to be processed.

    Returns:
        A list of tables, where each table is represented as a Pandas DataFrame.

    Raises:
        Exception: If there is an error while processing the Excel file.
    """
    tables: list[DataFrame] = []
    tables_bioc: BioCTableCollection | None = None
    try:
        # read the Excel file into a Pandas dataframe
        xls = pd.ExcelFile(filename)

        # loop through each sheet in the Excel file
        for sheet_name in xls.sheet_names:
            # read the sheet into a Pandas dataframe
            df = pd.read_excel(filename, sheet_name=sheet_name)
            df = convert_datetime_to_string(df)

            # Replace NaNs with empty string, then convert everything to string
            df = df.where(pd.notnull(df), "").astype(str)
            # convert all columns to string type for consistency and compatibility
            df = df.astype(str)
            # add the dataframe to the list of tables
            tables.append(df)
    except ImportError as ie:
        logger.error(
            msg=f"Failed to process the file {filename.name} due to the following missing Pandas dependency: {ie}"
        )

    if tables:
        tables_bioc = BioCTableConverter.build_bioc(tables, str(filename))

    return tables_bioc
