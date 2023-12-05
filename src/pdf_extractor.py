import datetime
import io
import json
import os
from copy import deepcopy
from os.path import join

import PyPDF2
import pandas
from bioc import BioCCollection
import pdfplumber
import logging

logging.basicConfig(filename="PDFExtractor.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %("
                                                                             "message)s")

pdf_data = None
filename = ""
table_references = []
table_locations = {}
table_count = 0

plumber_config = {
    "vertical_strategy": "text",
    "horizontal_strategy": "lines"
}


class BioCText:
    def __init__(self, text):
        self.infons = {}
        self.passages = self.__identify_passages(text)
        self.annotations = []

    @staticmethod
    def __identify_passages(text):
        """
        Identifies passages within the given text and creates passage objects.

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
        for line in text:
            # Determine the type of the line and assign appropriate information
            iao_name = "supplementary material section"
            iao_id = "IAO:0000326"
            # Create a passage object and add it to the passages list
            passages.append({
                "offset": offset,
                "infons": {
                    "iao_name_1": iao_name,
                    "iao_id_1": iao_id
                },
                "text": line,
                "sentences": [],
                "annotations": [],
                "relations": []
            })
            offset += len(line)
        return passages


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
        Builds a table passage in a specific format and appends it to the list of passages.

        Args:
            table_data (pandas.DataFrame): The table data to be included in the passage.

        Returns:
            None

        Example:
            table_data = pandas.DataFrame(
                [["A", "B", "C"], [1, 2, 3]],
                columns=["Column 1", "Column 2", "Column 3"]
            )
            self.__build_table(table_data)
        """
        # Create the title passage and append it to the list of passages
        title_passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_title",
                "iao_name_1": "document title",
                "iao_id_1": "IAO:0000305"
            },
        }
        self.passages.append(title_passage)
        # Create the caption passage and append it to the list of passages
        caption_passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_caption",
                "iao_name_1": "caption",
                "iao_id_1": "IAO:0000304"
            },
        }
        self.passages.append(caption_passage)
        # Create the passage containing the table content
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
        # Process the column headings of the table
        for i, text in enumerate(table_data.columns.values):
            passage["column_headings"].append(
                {
                    "cell_id": self.id + F".1.{i + 1}",
                    "cell_text": replace_unicode(text)
                }
            )
        # Process the data rows of the table
        for row_idx, row in enumerate(table_data.values):
            new_row = []
            for cell_idx, cell in enumerate(row):
                new_cell = {
                    "cell_id": F"{self.id}.{row_idx + 2}.{cell_idx + 1}",
                    "cell_text": F"{replace_unicode(cell)}"
                }
                new_row.append(new_cell)
            passage["data_section"][0]["data_rows"].append(new_row)
        # Append the table passage to the list of passages
        self.passages.append(passage)


def get_tables_bioc(tables, filename):
    """
        Converts a list of tables into the BioC format.

    Args:
        tables (list): A list of tables to be converted.
        filename (str): The name of the source file.

    Returns:
        dict: A dictionary representing the tables in the BioC format.
    """
    bioc = {
        "source": "Auto-CORPus (supplementary)",
        "date": str(datetime.date.today().strftime("%Y%m%d")),
        "key": "autocorpus_supplementary.key",
        "infons": {},
        "documents": [
            {
                "id": 1,
                "inputfile": filename,
                "infons": {},
                "passages": [BioCTable(i + 1, x).__dict__ for i, x in enumerate(tables)],
                "annotations": [],
                "relations": []
            }
        ]
    }
    return bioc


def get_blank_cell_count(row):
    """
    Counts the number of blank cells in a given row.

    Args:
        row (list): A list of dictionaries representing cells in a row.

    Returns:
        int: The number of blank cells in the row.

    Example:
        row = [
            {"text": "Hello"},
            {"text": ""},
            {"text": "World"},
            {"text": ""},
        ]
        blank_count = get_blank_cell_count(row)
        print(blank_count)  # Output: 2
    """
    blank_count = 0
    for cell in row:
        if not cell["text"].strip():
            blank_count += 1
    return blank_count


def get_text_bioc(parsed_texts, filename):
    """
    Convert parsed texts into BioC format.

    Args:
        parsed_texts (list): The parsed texts to be converted.

    Returns:
        BioCCollection: The converted texts in BioC format.

    The function takes a list of parsed texts (`parsed_texts`) as input.

    It initializes a BioCCollection object (`collection`) and sets the source, date, and key attributes for the collection.

    The function creates a BioCDocument object (`document`) to store the parsed texts.

    It iterates over each text in the `parsed_texts` list and creates a BioCPassage object (`passage`) for each text.
    The `replace_unicode` function is called to replace any Unicode characters in the text with their corresponding replacements.
    The converted text is assigned to the passage's `text` attribute.

    The function sets the offset for each passage by keeping track of the current offset.
    The offset represents the starting position of each passage in the combined text.
    The current offset is incremented by the length of each text.

    The passage is added to the document using the `document.add_passage(passage)` method.

    Finally, the document is added to the collection using the `collection.add_document(document)` method,
    and the collection is returned as the converted texts in BioC format.
    """
    # Create a BioC XML structure dictionary
    bioc = {
        "source": "Auto-CORPus (supplementary)",
        "date": str(datetime.date.today().strftime("%Y%m%d")),
        "key": "autocorpus_supplementary.key",
        "infons": {},
        "documents": [
            {
                "id": 1,
                "inputfile": filename,
                "infons": {},
                "passages": [BioCText(replace_unicode(x)).__dict__ for x in [y for y in parsed_texts]],
                "annotations": [],
                "relations": []
            }
        ]
    }
    return bioc


def convert_pdf_result(tables, text, input_file):
    """
    Convert the result of processing a PDF into a BioC format.

    Args:
        tables (list): The extracted tables from the PDF.
        text (list): The extracted text from the PDF.
        input_file (str): The path of the input PDF file.

    Returns:
        tuple: A tuple containing the converted BioC text and tables.
            - bioc_text (str): The converted text in BioC format.
            - bioc_tables (str): The converted tables in BioC format.

    The function takes three parameters: `tables`, `text`, and `input_file`.

    It calls the `get_tables_bioc` function to convert the extracted tables (`tables`) into BioC format.
    It passes `tables` and `input_file` as arguments to `get_tables_bioc`.

    It also calls the `get_text_bioc` function to convert the extracted text (`text`) into BioC format.

    Finally, the function returns a tuple containing the converted BioC text and tables as `bioc_text` and `bioc_tables`, respectively.
    """

    bioc_tables, bioc_text = get_tables_bioc(tables, input_file), get_text_bioc(text, input_file)
    return bioc_text, bioc_tables


def text_to_column(col_text):
    """
    Convert a column text into a list of column values.

    Args:
        col_text (str): The column text to be converted.

    Returns:
        list: A list of column values.

    The function takes a column text (`col_text`) as input.

    It checks if `col_text` is not empty. If it is not empty, it further checks if the column text contains a newline character (`\n`).

    If a newline character is present, the function splits the column text at the newline character using `col_text.split("\n")`.
    The resulting parts are returned as a list of column values.

    If no newline character is present, the function returns a list containing the column text as a single element.

    If the `col_text` is empty, the function returns a list containing `None`.

    Finally, the function returns the list of column values.
    """
    if col_text:
        if "\n" in col_text:
            return col_text.split("\n")
        else:
            return [col_text]
    else:
        return [None]


def restructure_rows(input_list, column_count):
    """
    Restructure rows in an input list to separate data rows and heading rows.

    Args:
        input_list (list): The input list containing the rows to be restructured.
        column_count (int): The expected number of columns in each row.

    Returns:
        tuple: A tuple containing the restructured rows.
            - new_rows (list): A list of data rows.
            - new_heading_rows (list): A list of heading rows.

    The function takes an input list (`input_list`) and an expected number of columns (`column_count`).

    It first initializes empty lists for `new_input_list`, `new_rows`, and `new_heading_rows`.

    The function checks if the input list requires splitting by comparing the number of non-empty cells containing newline characters
    with the total number of non-empty cells. If they are equal, `requires_split` is set to True.

    If `requires_split` is True, it splits the input list into multiple lists using `text_to_column(x)` for each element `x` in the input list.
    The resulting list of lists is stored in `new_input_list`.

    The function then iterates over the columns and rows in `new_input_list` to construct new rows.
    If the column count exceeds the length of a column in a row, an empty string is appended.
    If the column is None, None is appended.
    If the column is an empty string, an empty string is appended.

    The function separates the heading rows from the data rows by checking for the presence of None in a row.
    The heading rows are added to `new_heading_rows`, while the data rows are added to `new_rows`.
    Once the first None is encountered, it marks the end of the heading rows.

    If `requires_split` is False, the function assumes that all rows are data rows.
    It separates the heading rows from the data rows in a similar manner as above.

    Finally, the function returns a tuple containing the restructured data rows (`new_rows`) and heading rows (`new_heading_rows`).
    """
    new_input_list = []
    new_rows = []
    new_heading_rows = []
    requires_split = len([x for x in input_list[0] if x and "\n" in x]) == len([x for x in input_list[0] if x])

    # Split the input_list into multiple lists if required
    if requires_split:
        new_input_list = [text_to_column(x) for y in input_list for x in y]
        headings_finished = False
        for i in range(max([len(x) for x in new_input_list if x is not None])):
            new_row = []

            # Iterate over each column in new_input_list
            # col is the entire column of data, not a heading
            for col in new_input_list:
                if col:
                    if len(col) <= i:
                        new_row.append("")
                    else:
                        new_row.append(col[i])
                elif col is None:
                    new_row.append(None)
                elif col == '':
                    new_row.append("")
            # Separate heading rows from data rows
            if None in new_row and not headings_finished:
                new_heading_rows.append(new_row)
            else:
                new_rows.append(new_row)
                headings_finished = True
    else:
        headings_finished = False
        for row in input_list:
            # Separate heading rows from data rows
            if None in row and not headings_finished:
                new_heading_rows.append(row)
            else:
                new_rows.append(row)
                headings_finished = True

    return new_rows, new_heading_rows


def rotate_page(file, page):
    """
    Rotate a specific page of a PDF file and extract tables using pdfplumber.

    Args:
        file (str): The path of the input PDF file.
        page (int): The page number to be rotated and processed.

    Returns:
        list or bool: If successful, returns the extracted tables as a list.
                      Otherwise, returns False if an error occurs.

    The function rotates a specific page (`page`) of a PDF file (`file`) and extracts tables using the pdfplumber library.

    It first reads the PDF file using PyPDF2.PdfReader and makes a deepcopy of the desired page using reader.pages[page].

    The function then extracts the text from the page at the initial orientation (0 degrees) and calculates the average line length.

    It performs a loop to rotate the page in 90-degree increments, extract the text, and calculate the average line length for each rotation.
    The rotation_line_length_counts list keeps track of the average line length for each rotation.

    After the loop, the function determines the final rotation based on the rotation with the maximum average line length.
    If all rotations have the same average line length, the final rotation is set to 0.

    The function sets new_page to the original page from the reader.
    If a final_rotation is required, it rotates the new_page accordingly.

    Then, it writes the rotated page to a BytesIO stream using PyPDF2.PdfWriter and PyPDF2.PdfWriter.write().

    If any exception occurs during the writing process, it logs an error message and returns False.

    If the writing process is successful, the function seeks to the beginning of the stream and opens it as a buffered reader.

    It opens the buffered reader with pdfplumber to get a plumber_page object.

    The function extracts tables from the plumber_page using pdfplumber.Page.extract_tables() and the best plumber configuration
    obtained from get_best_plumber_config().

    Finally, it returns the extracted tables as a list if successful or False if an error occurs.
    """
    reader = PyPDF2.PdfReader(file)
    new_page = deepcopy(reader.pages[page])
    # Extract text from the page at the initial orientation (0 degrees)
    page_text = new_page.extract_text(orientations=(0)).split("\n")
    avg_line_length = sum(len(s) for s in page_text) / len(page_text) if len(page_text) > 0 else 0
    rotation_count = 0
    rotation_line_length_counts = [avg_line_length]

    # Rotate the page in 90-degree increments and calculate average line length for each rotation
    while rotation_count < 3:
        page_text = new_page.extract_text(orientations=(90 * (rotation_count + 1))).split("\n")
        avg_line_length = sum(len(s) for s in page_text) / len(page_text) if len(page_text) > 0 else 0
        rotation_line_length_counts.append(avg_line_length)
        rotation_count += 1

    # Determine the final rotation based on the rotation with the maximum average line length
    if len(set(rotation_line_length_counts)) > 1:
        final_rotation = (rotation_line_length_counts.index(max(rotation_line_length_counts))) * 90
    else:
        final_rotation = 0

    new_page = reader.pages[page]

    # Rotate the new_page if a final rotation is required
    if final_rotation:
        new_page.rotate(final_rotation)
    with io.BytesIO() as stream:
        try:
            # Write the rotated page to the stream
            writer = PyPDF2.PdfWriter(stream)
            writer.add_page(new_page)
            writer.write(stream)
        except AssertionError as ae:
            logging.error(msg=F"{file} raised the following error: {ae}")
            return False
        except Exception as ex:
            logging.error(msg=F"{file} raised the following error: {ex}")
            return False

        # Seek to the beginning of the stream and open it as a buffered reader
        stream.seek(0)
        reader = io.BufferedReader(stream)

        # Open the buffered reader with pdfplumber
        plumber_page = pdfplumber.open(reader)
        new_page = plumber_page.pages[0]

        # Extract tables from the plumber_page using the best plumber configuration
        data = None
        data = new_page.extract_tables(table_settings=get_best_plumber_config(new_page))
        return data if data else False


def validate_bounding_box(page, bbox):
    """
    Validates a bounding box coordinates within the boundaries of a page.

    Args:
        page (pdfplumber.Page): The pdfplumber.Page object representing a single page in a PDF.
        bbox (tuple): A tuple containing the coordinates of the bounding box in the format (x0, y0, x1, y1).

    Returns:
        tuple: A validated bounding box coordinates tuple within the boundaries of the page.

    The function takes a pdfplumber.Page object (`page`) representing a single page in a PDF
    and a tuple (`bbox`) containing the coordinates of a bounding box in the format (x0, y0, x1, y1).

    It first retrieves the coordinates of the page's bounding box using `page.bbox`.
    The coordinates are stored as (page_x0, page_y0, page_x1, page_y1).

    The function validates the given bounding box coordinates by comparing them with the page's bounding box.
    It checks each coordinate (x0, y0, x1, y1) of the given bounding box and ensures that they fall within the boundaries
    of the page's bounding box. If a coordinate exceeds the page's boundary, the corresponding coordinate from the page's
    bounding box is used instead.

    Finally, the function returns the validated bounding box coordinates as a tuple.
    """

    page_x_0, page_y_0, page_x_1, page_y_1 = page.bbox
    validated_bbox = [0, 0, 0, 0]

    # Validate x0 coordinate
    validated_bbox[0] = bbox[0] if bbox[0] < page_x_0 else page_x_0

    # Validate y0 coordinate
    validated_bbox[1] = bbox[1] if bbox[1] < page_y_0 else page_y_0

    # Validate x1 coordinate
    validated_bbox[2] = bbox[2] if bbox[2] < page_x_1 else page_x_1

    # Validate y1 coordinate
    validated_bbox[3] = bbox[3] if bbox[3] < page_y_1 else page_y_1

    # Convert the validated bounding box list to a tuple
    validated_bbox = tuple(validated_bbox)

    # Return the validated bounding box coordinates tuple
    return validated_bbox


def get_best_plumber_config(page):
    """
    Determine the best configuration for extracting tables using the pdfplumber library.

    Args:
        page (pdfplumber.Page): The pdfplumber.Page object representing a single page in a PDF.

    Returns:
        dict: A dictionary containing the best configuration options for extracting tables.
            - "vertical_strategy" (str): The chosen vertical strategy for table extraction.

    The function takes a pdfplumber.Page object as input, representing a single page in a PDF.

    It first initializes the `new_plumber_config` variable with the initial configuration stored in `plumber_config`.

    The function attempts to find tables on the page using the `find_tables()` method of the `page` object.
    If tables are found, it performs the following steps:
    1. Tries to access the first table in the `tables` list.
    2. Retrieves the bounding box of the table and crops the page to the table area using `page.crop()`.
       If a ValueError is raised (which can occur if the table's bounding box is larger than the actual page),
       the function sets the `table_area` to the entire page.
    3. If any other exception occurs, it logs an error message and continues execution.
    4. Extracts the text from the `table_area` using `table_area.extract_text()`.
    5. Calculates the average number of spaces per line in the extracted text.
    6. Determines the number of vertical and horizontal edges in the `table_area`.
    7. Based on the comparison of vertical edges and the average space count,
       it updates the "vertical_strategy" in `new_plumber_config` to either "text" or "lines".

    Finally, the function returns the `new_plumber_config` dictionary containing the best configuration options for table extraction.
    """
    table_area = None
    new_plumber_config = plumber_config
    # Find tables on the page
    tables = []
    try:
        tables = page.find_tables()
    except:
        return plumber_config
    if tables:
        try:
            # Get the first table and its bounding box
            table = tables[0]
            # Table's bounding box can, on rare occasions, be larger than the actual page
            table_area = page.crop(validate_bounding_box(page, table.bbox))
        except ValueError as ve:
            # Table's bounding box can, on rare occasions, be larger than the actual page.
            table_area = page
        except Exception as ex:
            logging.error(F"The following error was raised searching and scaling table bounding boxes: {ex}")

        # Extract text from the table area
        text_area = table_area.extract_text()

        # Calculate the average number of spaces per line
        space_counts = [len(x.split(" ")) - 1 for x in text_area.split("\n")]
        avg_space_count = sum(space_counts) / len(space_counts)

        # Determine the number of vertical and horizontal edges in the table area
        vertical_edges = len(table_area.vertical_edges)
        horizontal_edges = len(table_area.horizontal_edges)

        # Update the vertical strategy in new_plumber_config based on the
        # comparison of vertical edges and average space count
        if vertical_edges < avg_space_count:
            new_plumber_config["vertical_strategy"] = "text"
        else:
            new_plumber_config["vertical_strategy"] = "lines"

    return new_plumber_config


def process_pdf(input_file):
    """
    Process a PDF file and extract tables and page texts.

    Args:
        input_file (str): The path of the input PDF file.

    Returns:
        tuple: A tuple containing tables and page texts.
            - tables (list): A list of pandas DataFrames representing the extracted tables.
            - page_texts (list): A list of strings representing the extracted text from each page.

    The function uses the `pdfplumber` library to open the input PDF file.

    It iterates over each page in the PDF file and performs the following steps:
    1. Extracts the text from the page using `page.extract_text()`.
    2. Splits the extracted text into lines using the newline character ('\n').
    3. Calls the `rotate_page` function to check if the page needs to be rotated and performs necessary rotations.
    4. If the `rotate_page` function returns data, it iterates over each table in the data and performs the following:
        a. Extracts the column names from the first row of the table.
        b. Restructures the rows of the table using the `restructure_rows` function.
        c. If there are missing row data, it raises a ValueError with a message.
        d. If new headings are present, it appends them to the corresponding columns.
        e. Constructs a pandas DataFrame using the rows and columns.
    5. If any exception occurs during the table processing, it logs an error message and returns False for both tables and page texts.

    The extracted tables and page texts are appended to the `tables` and `page_texts` lists, respectively.

    Finally, the function returns the `tables` and `page_texts` lists as a tuple.
    """
    filename = input_file
    pdf = pdfplumber.open(input_file)
    logging.info(input_file)
    tables = []
    page_texts = []
    # Iterate over each page in the PDF file
    for i, page in enumerate(pdf.pages):
        # Extract text from the page and split into lines
        page_text = page.extract_text()
        page_text = page_text.split("\n")
        # Check if the page needs rotation and perform necessary rotations
        data = rotate_page(input_file, i)
        if data:
            for table in data:
                try:
                    # Extract column names from the first row
                    cols = [x for x in table[0]]
                    # Restructure rows and get new headings if available
                    rows, new_headings = restructure_rows(table[1:], len(table[0]))
                    # Raise an error if there are missing row data
                    if not rows:
                        raise ValueError("missing row data")
                    # Append new headings to the corresponding columns
                    if new_headings:
                        for h_idx, heading_row in enumerate(new_headings):
                            for i in range(len(cols)):
                                if i > h_idx:
                                    break
                                if heading_row[i]:
                                    cols[i] = F"{cols[i]} | {heading_row[i]}"
                    # Create a pandas DataFrame using the rows and columns
                    df = pandas.DataFrame(rows, columns=cols)
                except ValueError as ve:
                    logging.error(msg=F"Failed to process table on page {i} of file: {input_file} due to:\n{ve}")
                    continue
                except Exception as ex:
                    logging.error(msg=F"Failed to process file: {input_file} due to:\n{ex}")
                    continue
                # Append the DataFrame to the tables list
                tables.append(df)
        # Append the page text to the page_texts list
        page_texts.append(page_text)
    # Return the tables and page_texts as a tuple
    return tables, page_texts


def replace_unicode(text):
    """
    Replaces specific Unicode characters with their corresponding replacements in the given text.

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
    if type(text) == list:
        clean_texts = []
        for t in text:
            if t:
                clean_texts.append(
                    t.replace('\u00a0', ' ').replace('\u00ad', '-').replace('\u2010', '-').replace('\u00d7', 'x'))
        return clean_texts
    else:
        clean_text = text.replace('\u00a0', ' ').replace('\u00ad', '-').replace('\u2010', '-').replace('\u00d7', 'x')
        return clean_text


def process_directories(input_directory):
    """
    Process all PDF files in the specified directory and its subdirectories.

    Args:
        input_directory (str): The directory path containing PDF files.

    Returns:
        None
    """
    files_processed, successful_extractions = 0, 0
    # Traverse through the directory and its subdirectories
    for parent, folders_in_parent, files_in_parent in os.walk(input_directory):
        # Process each file in the current directory
        for file in files_in_parent:
            # Check if the file is a PDF file
            if file.endswith(".pdf"):
                files_processed += 1
                # Extract tables and text from the PDF file
                tables, text = process_pdf(join(parent, file))
                # If tables were extracted successfully
                if tables:
                    successful_extractions += 1
                    # Write the extracted tables to a JSON file
                    with open(F"{os.path.join(parent, 'PDF_tables.json')}", "w", encoding="utf-8") as f_out:
                        json_output = convert_pdf_result(tables, text, file)
                        json.dump(json_output[1], f_out, indent=4)
                    # Log the output file path
                    logging.info(F"Output: {os.path.join(parent, 'PDF_tables.json')}")
    # Log the summary of successful extractions
    logging.info(F"Successfully extracted tables from {successful_extractions} out of {files_processed} PDF files.")
