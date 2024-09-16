import json
import os.path

from bioc import biocjson

from file_extension_analysis import get_file_extensions
from pdf_extractor import process_pdf, convert_pdf_result
from word_extractor import process_word_document
from excel_extractor import process_spreadsheet, get_tables_bioc

word_extensions = [".doc", ".docx"]
spreadsheet_extensions = [".csv", ".xls", ".xlsx"]
supplementary_types = word_extensions + spreadsheet_extensions + [".pdf"]


def __extract_word_data(locations=None, file=None):
    """
    Extracts data from Word documents located at the given file locations.

    Args:
        locations (dict): A dictionary containing file locations of Word documents.
            The keys are file extensions associated with Word documents, and the values
            are dictionaries with the following structure:
                - 'total' (int): The total count of Word documents with the extension.
                - 'locations' (list): A list of paths to the locations of Word documents.

    Returns:
        None

    """
    if locations:
        word_locations = [locations[x]["locations"] for x in word_extensions if locations[x]["locations"]]
        temp = []
        for x in word_locations:
            if not type(x) == list:
                temp.append(x)
            else:
                for y in x:
                    temp.append(y)
        word_locations = temp
        # Iterate over the file locations of Word documents
        for x in word_locations:
            # Process the Word document using a custom word_extractor
            process_word_document(x)

    if file:
        process_word_document(file)


def __extract_pdf_data(locations=None, file=None):
    """
    Extracts data from PDF documents located at the given file locations.

    Args:
        locations (dict): A dictionary containing file locations of PDF documents.
            The keys are file extensions associated with PDF documents, and the values
            are dictionaries with the following structure:
                - 'total' (int): The total count of PDF documents with the extension.
                - 'locations' (list): A list of paths to the locations of PDF documents.

    Returns:
        None

    """
    if locations:
        pdf_locations = locations[".pdf"]["locations"]
        # Iterate over the file locations of PDF documents
        for x in pdf_locations:
            base_dir, file_name = os.path.split(x)
            # Process the PDF document using a custom pdf_extractor
            tables, text = process_pdf(x)
            text, tables = convert_pdf_result(tables, text, x)
            # Write the extracted tables & texts to JSON files
            if tables:
                with open(F"{os.path.join(base_dir, file_name + '_tables.json')}", "w", encoding="utf-8") as tables_out:
                    json.dump(tables, tables_out, indent=4)
            if text:
                with open(F"{os.path.join(base_dir, file_name + '_tables.json')}", "w", encoding="utf-8") as text_out:
                    biocjson.dump(text, text_out)
    if file:
        base_dir, file_name = os.path.split(file)
        # Process the PDF document using a custom pdf_extractor
        tables, text = process_pdf(file)
        # Write the extracted tables to a JSON file
        text, tables = convert_pdf_result(tables, text, file)
        if tables:
            with open(F"{os.path.join(base_dir, file_name + '_tables.json')}", "w", encoding="utf-8") as tables_out:
                json.dump(tables, tables_out, indent=4)
        if text:
            with open(F"{os.path.join(base_dir, file_name + '_bioc.json')}", "w", encoding="utf-8") as text_out:
                biocjson.dump(text, text_out)


def __extract_spreadsheet_data(locations=None, file=None):
    """
    Extracts data from Spreadsheet documents located at the given file locations.

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
    if locations:
        spreadsheet_locations = [locations[x]["locations"] for x in spreadsheet_extensions]
        # Iterate over the file locations of Spreadsheet documents
        for x in spreadsheet_locations:
            base_dir, file_name = os.path.split(x)
            # Process the PDF document using a custom excel_extractor
            tables = process_spreadsheet(x)
            # If tables are extracted
            if tables:
                # Create a JSON output file for the extracted tables
                with open(F"{os.path.join(base_dir, file_name + '_tables.json')}", "w", encoding="utf-8") as f_out:
                    # Generate BioC format representation of the tables
                    json_output = get_tables_bioc(tables, x)
                    json.dump(json_output, f_out, indent=4)
    if file:
        base_dir, file_name = os.path.split(file)
        # Process the PDF document using a custom excel_extractor
        tables = process_spreadsheet(file)
        # If tables are extracted
        if tables:
            # Create a JSON output file for the extracted tables
            with open(F"{os.path.join(base_dir, file_name + '_tables.json')}", "w", encoding="utf-8") as f_out:
                # Generate BioC format representation of the tables
                json_output = get_tables_bioc(tables, file)
                json.dump(json_output, f_out, indent=4)


def process_supplementary_files(supplementary_files, output_format='json'):
    """
    Processes input list of file paths as supplementary data.

    Args:
        supplementary_files (list): List of file paths
    """
    for file in supplementary_files:
        if not os.path.exists(file) or os.path.isdir(file):
            continue

        # Extract data from Word files if they are present
        if [1 for x in word_extensions if file.lower().endswith(x)]:
            __extract_word_data(file=file)

        # Extract data from PDF files if they are present
        elif file.lower().endswith("pdf"):
            __extract_pdf_data(file=file)

        # Extract data from spreadsheet files if they are present
        elif [1 for x in spreadsheet_extensions if file.lower().endswith(x)]:
            __extract_spreadsheet_data(file=file)


def generate_file_report(input_directory):
    """
    Generates a file report based on the file extensions present in the input directory.

    Args:
        input_directory (str): The path to the input directory.

    Returns:
        None or dict: Returns None if no file extensions are found in the input directory.
        If file extensions are found, returns a dictionary containing extracted data based on
        specific file types.

    """
    if not os.path.exists(input_directory) or not os.path.isdir(input_directory):
        return None
    file_extensions = get_file_extensions(input_directory)
    # Check if no file extensions are found
    if not file_extensions:
        return None
    # Check if PDF files are present
    pdf_present = "pdf" in file_extensions.keys()
    # Check if Word files are present
    word_present = True if any([x for x in file_extensions.keys() if x in word_extensions]) else False
    # Check if spreadsheet files are present
    spreadsheet_present = True if any([x for x in file_extensions.keys() if x in spreadsheet_extensions]) else False
    # Extract data from Word files if they are present
    if word_present:
        word_locations = {x: file_extensions[x] for x in word_extensions}
        __extract_word_data(word_locations)
    # Extract data from PDF files if they are present
    if pdf_present:
        pdf_locations = {".pdf": file_extensions[".pdf"]}
        __extract_pdf_data(pdf_locations)
    # Extract data from spreadsheet files if they are present
    if spreadsheet_present:
        spreadsheet_locations = {x: file_extensions[x] for x in spreadsheet_extensions}
        __extract_spreadsheet_data(spreadsheet_locations)
    return True
