"""This module provides functionality for processing supplementary files.

Extracts data from various file types such as PDFs, spreadsheets,
PowerPoint presentations, and archives. It also handles logging and error
management for unprocessed files.
"""

import datetime
import gc
import json
import os.path
import re
import shutil
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path

import pandas as pd
import PyPDF2
import rarfile
from bioc import BioCCollection, BioCDocument, BioCPassage, biocjson
from BioCTable import convert_datetime_to_string, get_tables_bioc
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from pdf_extractor import convert_pdf_result
from powerpoint_extractor import get_powerpoint_text
from word_extractor import process_word_document

from autocorpus.utils import replace_unicode

WORD_EXTENSIONS = [".doc", ".docx"]
SPREADSHEET_EXTENSIONS = [".csv", ".xls", ".xlsx", ".tsv"]
SUPPLEMENTARY_TYPES = WORD_EXTENSIONS + SPREADSHEET_EXTENSIONS + [".pdf", ".pptx"]
PRESENTATION_EXTENSIONS = [".pptx", ".ppt", ".pptm", ".odp"]
ZIP_EXTENSIONS = [".zip", ".7z", ".zlib", ".7-zip", ".pzip", ".xz"]
TAR_EXTENSIONS = [".tgz", ".tar", ".bgz"]
RAR_EXTENSIONS = [".rar"]
GZIP_EXTENSIONS = [".gzip", ".gz"]
ARCHIVE_EXTENSIONS = ZIP_EXTENSIONS + TAR_EXTENSIONS + GZIP_EXTENSIONS + RAR_EXTENSIONS

# Load when needed, not for e.g. processing non-pdf files.
pdf_converter: PdfConverter | None = None


def _load_pdf_models():
    global pdf_converter
    if pdf_converter is None:
        pdf_converter = PdfConverter(
            artifact_dict=create_model_dict(),
        )


def extract_table_from_text(text: str) -> tuple[list[str], list[pd.DataFrame]]:
    """Extracts tables from a given text and returns the modified text and extracted tables.

    Args:
        text (str): The input text containing potential table data.

    Returns:
        tuple[str, list[pd.DataFrame]]: A tuple containing the modified text without table lines
        and a list of DataFrames representing the extracted tables.
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
                    # Remove empty cells that may result from leading/trailing pipes
                    # if cells[0] == '':
                    #     cells.pop(0)
                    # if cells[-1] == '':
                    #     cells.pop(-1)
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
    return text_output, tables_output


def get_bioc_passages(text: list[str] | str) -> list[BioCPassage] | list[str]:
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
            get_bioc_passages(replace_unicode(x)).__dict__["passages"]
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


def __extract_pdf_data(file: str) -> tuple[bool, str]:
    """Extracts data from a PDF file of < 100 pages.

    Args:
        file (str): The file path of the PDF to be processed.

    Returns:
        tuple: A tuple containing:
            - bool: True if the PDF was successfully processed, False otherwise.
            - str: A message indicating the result of the processing or the reason for failure.

    Raises:
        Exception: If an error occurs during the PDF processing.
    """
    base_dir, file_name = os.path.split(file)
    if file:
        try:
            # Check the size of the PDF in pages
            total_pages = 0
            with open(file, "rb") as f_in:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                f_in.close()

            if total_pages > 100:
                print(f"PDF file contains over 100 pages, skipping: {file}")
                return False, "PDF file contains over 100 pages. This file was skipped."

            _load_pdf_models()
            if pdf_converter:
                rendered = pdf_converter(file)
                text, images, out_meta = text_from_rendered(rendered)
                text, tables = extract_table_from_text(text)
                bioc_text, bioc_tables = None, None
                if text:
                    bioc_text = get_text_bioc(text, file)
                if tables:
                    bioc_tables = get_tables_bioc(tables)

                # text, tables = convert_pdf_result(tables, [text], file)
                if bioc_text or bioc_tables:
                    base_dir = base_dir.replace("Raw", "Processed")
                    output_path = f"{os.path.join(base_dir, file_name + '_bioc.json')}"
                    if not Path(output_path).parent.exists():
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    if bioc_text:
                        global args
                        with open(output_path, "w+", encoding="utf-8") as text_out:
                            biocjson.dump(bioc_text, text_out, indent=4)
                    if bioc_tables:
                        with open(
                            f"{os.path.join(base_dir, file_name + '_tables.json')}",
                            "w+",
                            encoding="utf-8",
                        ) as tables_out:
                            json.dump(bioc_tables, tables_out, indent=4)
                    return True, ""
                else:
                    return False, ""
        except Exception as ex:
            print(ex)
            return False, ""
    return False, "No file provided."


def __extract_spreadsheet_data(file: str):
    """Extracts data from Spreadsheet documents located at the given file locations.

    Args:
        locations (dict): A dictionary containing file locations of Spreadsheet documents.
            The keys are file extensions associated with Spreadsheet documents, and the values
            are dictionaries with the following structure:
                - 'total' (int): The total count of Spreadsheet documents with the extension.
                - 'locations' (list): A list of paths to the locations of Spreadsheet documents.

        file (str): A string containing a spreadsheet file path to process.

    Returns:
        None

    """
    if file:
        base_dir, file_name = os.path.split(file)
        tables = []
        # Process the PDF document using a custom excel_extractor
        try:
            # read the Excel file into a Pandas dataframe
            xls = pd.ExcelFile(file)

            # loop through each sheet in the Excel file
            for sheet_name in xls.sheet_names:
                # read the sheet into a Pandas dataframe
                df = pd.read_excel(file, sheet_name=sheet_name)
                df = convert_datetime_to_string(df)
                # add the dataframe to the list of tables
                tables.append(df)
        except Exception as ex:
            log_unprocessed_supplementary_file(
                file,
                file_name,
                "Failed to extract text from the spreadsheet: " + str(ex),
            )

        # If tables are extracted
        if tables:
            base_dir = base_dir.replace("Raw", "Processed")
            # Create a JSON output file for the extracted tables
            output_path = f"{os.path.join(base_dir, file_name + '_tables.json')}"
            if not Path(output_path).exists():
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(output_path, "w+", encoding="utf-8") as f_out:
                    # Generate BioC format representation of the tables
                    json_output = get_tables_bioc(tables)
                    json.dump(json_output, f_out, indent=4)
            except Exception as ex:
                print(f"{file_name}: {ex}")
            return True
    return False


def __extract_powerpoint_data(file: str):
    """Extracts data from Powerpoint documents located at the given file locations.

    Args:
    locations (dict): A dictionary containing file locations of Powerpoint documents.
    The keys are file extensions associated with Powerpoint documents, and the values
    are dictionaries with the following structure:
    - 'total' (int): The total count of Powerpoint documents with the extension.
    - 'locations' (list): A list of paths to the locations of Powerpoint documents.
    file (str): A string containing a Powerpoint file path to process.

    :return:
        None
    """
    base_dir, file_name = os.path.split(file)
    if file:
        try:
            text = get_powerpoint_text(file)
            text, tables = convert_pdf_result([], text, file)
            if text:
                base_dir = base_dir.replace("Raw", "Processed")
                if not Path(base_dir).exists():
                    Path(base_dir).mkdir(parents=True, exist_ok=True)
                global args
                with open(
                    f"{os.path.join(base_dir, file_name + '_bioc.json')}",
                    "w",
                    encoding="utf-8",
                ) as text_out:
                    biocjson.dump(text, text_out, indent=4)
                return True
            else:
                return False
        except Exception:
            return False


def retry_rmtree(path, retries=5, delay=1):
    """Attempt to remove a directory tree with retries.

    Args:
        path (str): The path to the directory to be removed.
        retries (int): The number of retry attempts in case of failure.
        delay (int): The delay in seconds between retry attempts.

    Returns:
        None
    """
    for _ in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            time.sleep(delay)  # Wait before retrying
        except FileNotFoundError:
            return  # Directory already removed
        except Exception:
            return


def process_and_update_rar(archive_path):
    """Extract and process a RAR archive file.

    Args:
        archive_path (str): Path to the RAR archive file.

    Returns:
        tuple: A tuple containing a boolean indicating success and a list of failed files.
    """
    success = False
    failed_files = []
    processed_dir = Path(archive_path).parent.parent / "Processed"
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            with rarfile.RarFile(archive_path, "r") as rar_ref:
                rar_ref.extractall(temp_dir)
                extracted_files = [
                    os.path.join(temp_dir, member.filename)
                    for member in rar_ref.infolist()
                    if not member.isdir()
                ]

            for file_path in extracted_files:
                success, failed_files, reason = process_supplementary_files([file_path])

                if success:
                    file_output_success = False
                    for new_result_file in ["_bioc.json", "_tables.json"]:
                        new_file_path = file_path + new_result_file
                        output_path = processed_dir / (
                            Path(file_path).name + new_result_file
                        )

                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        if os.path.exists(new_file_path):
                            shutil.move(new_file_path, output_path)
                            file_output_success = True

                    if not file_output_success:
                        failed_files.append(file_path)
                else:
                    failed_files.append(file_path)

    except Exception as e:
        print(f"Error processing archive {archive_path}: {e}")

    for file in failed_files:
        log_unprocessed_supplementary_file(
            archive_path,
            Path(file).name,
            "Failed to extract text from the document.",
        )

    return success, failed_files


def process_and_update_zip(archive_path):
    """Extract and process a ZIP archive file.

    Args:
        archive_path (str): Path to the ZIP archive file.

    Returns:
        tuple: A tuple containing a boolean indicating success and a list of failed files.
    """
    success = False
    failed_files = []

    processed_dir = Path(archive_path).parent.parent / "Processed"
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            # Extract files
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
                extracted_files = [
                    str(Path(temp_dir) / member.filename)
                    for member in zip_ref.infolist()
                    if not member.is_dir()
                ]

            for file_path in extracted_files:
                success, failed_files, reason = process_supplementary_files([file_path])

                if success:
                    file_output_success = False
                    for new_result_file in ["_bioc.json", "_tables.json"]:
                        new_file_path = file_path + new_result_file
                        output_path = processed_dir / (
                            Path(file_path).name + new_result_file
                        )

                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        if os.path.exists(new_file_path):
                            # Ensure file is closed before moving
                            with open(new_file_path):
                                pass  # Just open and close it to release lock
                            shutil.move(new_file_path, output_path)
                            file_output_success = True

                    if not file_output_success:
                        failed_files.append(file_path)
                else:
                    failed_files.append(file_path)

    except Exception as e:
        print(f"Error processing archive {archive_path}: {e}")

    # Log failed files
    for file in failed_files:
        log_unprocessed_supplementary_file(
            archive_path,
            Path(file).name,
            "Failed to extract text from the document.",
        )

    return success, failed_files


def process_and_update_tar(archive_path):
    """Extract and process a TAR archive file.

    Args:
        archive_path (str): Path to the TAR archive file.

    Returns:
        tuple: A tuple containing a boolean indicating success and a list of failed files.
    """
    success = False
    failed_files = []
    processed_dir = Path(archive_path).parent.parent / "Processed"
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            with tarfile.open(archive_path, "r") as tar_ref:
                tar_ref.extractall(temp_dir)
                extracted_files = [
                    os.path.join(temp_dir, member.name)
                    for member in tar_ref.getmembers()
                    if member.isfile()
                ]

            for file_path in extracted_files:
                success, failed_files, reason = process_supplementary_files([file_path])

                if success:
                    file_output_success = False
                    for new_result_file in ["_bioc.json", "_tables.json"]:
                        new_file_path = file_path + new_result_file
                        output_path = processed_dir / (
                            Path(file_path).name + new_result_file
                        )

                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        if os.path.exists(new_file_path):
                            shutil.move(new_file_path, output_path)
                            file_output_success = True

                    if not file_output_success:
                        failed_files.append(file_path)
                else:
                    failed_files.append(file_path)

    except Exception as e:
        print(f"Error processing archive {archive_path}: {e}")

    for file in failed_files:
        log_unprocessed_supplementary_file(
            archive_path,
            Path(file).name,
            "Failed to extract text from the document.",
        )

    return success, failed_files


def process_archive_file(file: str):
    """Process an archive file (RAR, ZIP, TAR, etc.) and extract its contents.

    Args:
        file (str): Path to the archive file.

    Returns:
        tuple: A tuple containing a boolean indicating success and a list of failed files.
    """
    success, failed_files = False, []
    file_extension = file[file.rfind(".") :].lower()
    if file_extension == ".rar":
        success, failed_files = process_and_update_rar(file)
    elif file_extension in ZIP_EXTENSIONS:
        success, failed_files = process_and_update_zip(file)
    elif file_extension in TAR_EXTENSIONS or file_extension in GZIP_EXTENSIONS:
        success, failed_files = process_and_update_tar(file)
    return success, failed_files


def process_supplementary_files(supplementary_files: list[str]):
    """Processes input list of file paths as supplementary data.

    Args:
        supplementary_files (list): List of file paths
    """
    success, failed_files, reason = False, [], ""
    for file in supplementary_files:
        gc.collect()
        if not os.path.exists(file) or os.path.isdir(file):
            success = False

        # Extract data from Word files if they are present
        if [1 for x in WORD_EXTENSIONS if file.lower().endswith(x)]:
            success = process_word_document(file=file)

        # Extract data from PDF files if they are present
        elif file.lower().endswith(".pdf"):
            success, reason = __extract_pdf_data(file=file)

        # Extract data from PowerPoint files if they are present
        elif [1 for x in PRESENTATION_EXTENSIONS if file.lower().endswith(x)]:
            success = __extract_powerpoint_data(file=file)

        # Extract data from spreadsheet files if they are present
        elif [1 for x in SPREADSHEET_EXTENSIONS if file.lower().endswith(x)]:
            success = __extract_spreadsheet_data(file=file)

        elif [1 for x in ARCHIVE_EXTENSIONS if file.lower().endswith(x)]:
            success, failed_files = process_archive_file(file=file)

    return success, failed_files, reason


def set_unrar_path(path: str):
    """Set the path to the UNRAR tool for handling RAR files.

    Args:
        path (str): The file path to the UNRAR executable.
    """
    rarfile.UNRAR_TOOL = path


def log_unprocessed_supplementary_file(file: str, archived_file: str, reason: str):
    """Log details of unprocessed supplementary files to a TSV file.

    Args:
        file (str): Path to the supplementary file.
        archived_file (str): Name of the file inside the archive, if applicable.
        reason (str): Reason why the file could not be processed.
        log_path (str): Path to the directory where the log file will be saved.

    Returns:
        None
    """
    supplementary_dir = str(Path(file).parts[2])
    file_name = str(Path(file).parts[-1])
    log_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "logs", "supplementary"
    )
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    if not archived_file:
        archived_file = ""
    with open(
        os.path.join(log_path, f"{os.path.split(log_path)[-1]}_unprocessed.tsv"),
        "a",
        encoding="utf-8",
    ) as f_out:
        f_out.write(f"{supplementary_dir}\t{file_name}\t{archived_file}\t{reason}\n")
