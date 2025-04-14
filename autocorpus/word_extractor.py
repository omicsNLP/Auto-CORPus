import argparse
import datetime
import json
import logging
import os
import platform
import subprocess
from os.path import join
from pathlib import Path

from docx import Document
from FAIRClinicalWorkflow.BioC_Utilities import apply_sentence_splitting

logging.basicConfig(
    filename="WordExtractor.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

filename = ""
args = None


def set_args():
    global args
    parser = argparse.ArgumentParser()
    args, _ = parser.parse_known_args()


def replace_unicode(text):
    """Replaces specific Unicode characters in a given text.

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
    if type(text) is list:
        clean_texts = []
        for t in text:
            if t and type(t) is str:
                clean_texts.append(
                    t.replace("\u00a0", " ")
                    .replace("\u00ad", "-")
                    .replace("\u2010", "-")
                    .replace("\u00d7", "x")
                )
            else:
                clean_texts.append(t)
        return clean_texts
    else:
        if type(text) is str:
            clean_text = (
                text.replace("\u00a0", " ")
                .replace("\u00ad", "-")
                .replace("\u2010", "-")
                .replace("\u00d7", "x")
            )
        else:
            clean_text = text
        return clean_text


class BioCText:
    def __init__(self, text):
        self.infons = {}
        self.passages = self.__identify_passages(text)
        self.annotations = []

    @staticmethod
    def __identify_passages(text):
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
        passages.append(
            {
                "offset": offset,
                "infons": {"iao_name_1": iao_name, "iao_id_1": iao_id},
                "text": line,
                "sentences": [],
                "annotations": [],
                "relations": [],
            }
        )
        offset += len(line)
        return passages


class BioCTable:
    """Converts tables from nested lists into a BioC table object."""

    def __init__(self, input_file, table_id, table_data):
        self.inputfile = input_file
        self.id = str(table_id) + "_1"
        self.infons = {}
        self.passage = {}
        self.annotations = []
        self.__build_table(table_data)

    def __build_table(self, table_data):
        """Builds a table passage in a specific format and appends it to the list of passages.

        Args:
            table_data (list): The table data to be included in the passage. It should be a list
                               containing the table's column headings as the first row, followed by
                               the data rows.

        Returns:
            None

        Example:
            table_data = [
                ["Column 1", "Column 2", "Column 3"],
                [1, 2, 3],
                [4, 5, 6]
            ]
            self.__build_table(table_data)
        """
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
        # Process the column headings of the table
        for i, col in enumerate(table_data[0]):
            passage["column_headings"].append(
                {"cell_id": self.id + f".1.{i + 1}", "cell_text": col}
            )
        # Process the data rows of the table
        for row_idx, row in enumerate(table_data[1:]):
            new_row = []
            for cell_idx, cell in enumerate(row):
                new_cell = {
                    "cell_id": f"{self.id}.{row_idx + 2}.{cell_idx + 1}",
                    "cell_text": f"{cell}",
                }
                new_row.append(new_cell)
            passage["data_section"][0]["data_rows"].append(new_row)
        self.passage = passage

    def get_table(self):
        return self.passage


def get_tables_bioc(tables, filename, textsource="Auto-CORPus"):
    """Generates a BioC XML structure containing tables.

    Args:
        tables (list): A list of tables to be included in the BioC structure.
                       Each table should be represented as a nested list, where each inner list
                       corresponds to a row, and each element in the inner list corresponds to the
                       text content of a cell in the row.

    Returns:
        dict: A dictionary representing the generated BioC XML structure.

    Example:
        tables = [[["A", "B"], ["1", "2"]], [["X", "Y"], ["3", "4"]]]
        bioc_xml = get_tables_bioc(tables)
    """
    # Create a BioC JSON structure dictionary
    bioc = {
        "source": "Auto-CORPus (supplementary)",
        "date": str(datetime.date.today().strftime("%Y%m%d")),
        "key": "autocorpus_supplementary.key",
        "infons": {},
        "documents": [
            {
                "id": 1,
                "inputfile": filename,
                "textsource": textsource,
                "infons": {},
                "passages": [],
                "annotations": [],
                "relations": [],
            }
        ],
    }
    for i, x in enumerate(tables):
        bioc["documents"][0]["passages"].append(
            BioCTable(filename, i + 1, x).get_table()
        )
    return bioc


def get_text_bioc(paragraphs, filename, textsource="Auto-CORPus"):
    """Generates a BioC JSON structure containing text paragraphs.

    Args:
        paragraphs (list): A list of paragraphs to be included in the BioC structure.

    Returns:
        dict: A dictionary representing the generated BioC XML structure.

    Example:
        paragraphs = ["This is the first paragraph.", "This is the second paragraph."]
        bioc_xml = get_text_bioc(paragraphs)
    """
    passages = [
        p
        for sublist in [
            BioCText(text=replace_unicode(x)).__dict__["passages"] for x in paragraphs
        ]
        for p in sublist
    ]
    offset = 0
    for p in passages:
        p["offset"] = offset
        offset += len(p["text"])
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
                "textsource": textsource,
                "infons": {},
                "passages": passages,
                "annotations": [],
                "relations": [],
            }
        ],
    }
    return bioc


def extract_tables(doc):
    """Extracts tables from a .docx document.

    Args:
        doc (docx.Document): The Document object representing the .docx document.

    Returns:
        list: A list of tables extracted from the document. Each table is represented as a nested list,
              where each inner list corresponds to a row, and each element in the inner list corresponds
              to the text content of a cell in the row.

    Example:
        from docx import Document

        doc = Document("document.docx")
        tables = extract_tables(doc)
    """
    # Open the .docx file
    tables = []
    # Iterate through the tables in the document
    for table in doc.tables:
        tables.append([])
        # Iterate through the rows in the table
        for row in table.rows:
            tables[-1].append([x.text for x in row.cells])
    return tables


def convert_older_doc_file(file, output_dir):
    operating_system = platform.system()
    docx_path = file.replace(".doc", ".docx")
    if operating_system == "Windows":
        import win32com.client

        word = None
        try:
            docx_path = file + ".docx"
            word = win32com.client.DispatchEx("Word.Application")
            doc = word.Documents.Open(file)
            doc.SaveAs(file + ".docx", 16)
            doc.Close()
            word.Quit()
            return docx_path
        except Exception:
            return False
        finally:
            word.Quit()
    elif operating_system == "linux":
        # Convert .doc to .docx using LibreOffice
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "docx",
                "--outdir",
                output_dir,
                file,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return docx_path
    elif operating_system == "Darwin":  # macOS
        try:
            # AppleScript to open the file in Word and save as .docx
            applescript = f'''
            tell application "Microsoft Word"
                open "{file}"
                save as active document file name "{docx_path}" file format format document
                close active document saving no
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
            return docx_path
        except Exception:
            return False
    else:
        return False


def extract_text_from_doc(file_path):
    """Extracts text from a .doc file by converting it to .docx and processing with python-docx."""
    if not file_path.endswith(".doc"):
        raise ValueError("Input file must be a .doc file.")
    try:
        output_dir = str(Path(file_path).parent.absolute())
        docx_path = convert_older_doc_file(file_path, output_dir)

        # Extract text from the resulting .docx file
        doc = Document(docx_path)
        tables = extract_tables(doc)
        text_sizes = set(
            [int(x.style.font.size) for x in doc.paragraphs if x.style.font.size]
        )
        paragraphs = [
            (
                x.text,
                True
                if text_sizes
                and x.style.font.size
                and int(x.style.font.size) > min(text_sizes)
                else False,
            )
            for x in doc.paragraphs
        ]
        os.unlink(docx_path)
        return paragraphs, tables
    except FileNotFoundError:
        print(
            "LibreOffice 'soffice' command not found. Ensure it is installed and in your PATH."
        )
        return None, None
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None, None


def process_word_document(file):
    """Processes a Word document file, extracting tables and paragraphs, and saving them as JSON files.

    Args:
        file (str): The path to the Word document file.

    Returns:
        None

    Example:
        file_path = "/path/to/document.docx"
        process_word_document(file_path)
    """
    tables, paragraphs = [], []
    output_path = file.replace("Raw", "Processed")
    # Check if the file has a ".doc" or ".docx" extension
    if file.lower().endswith(".doc") or file.lower().endswith(".docx"):
        try:
            doc = Document(file)
            tables = extract_tables(doc)
            text_sizes = set(
                [int(x.style.font.size) for x in doc.paragraphs if x.style.font.size]
            )
            paragraphs = [
                (
                    x.text,
                    True
                    if text_sizes
                    and x.style.font.size
                    and int(x.style.font.size) > min(text_sizes)
                    else False,
                )
                for x in doc.paragraphs
            ]
        except ValueError:
            try:
                if not file.lower().endswith(".docx"):
                    paragraphs, tables = extract_text_from_doc(file)
                    if paragraphs:
                        logging.info(
                            f"File {file} was converted to .docx as a copy within the same directory for processing."
                        )
                    else:
                        logging.info(
                            f"File {file} could not be processed correctly. It is likely a pre-2007 word document or problematic."
                        )
                        return False
                else:
                    logging.info(f"File {file} could not be processed correctly.")
                    return False
            except ValueError as ve:
                logging.info(f"File {file} raised the error:\n{ve}")
                return False
        except Exception as ex:
            logging.info(f"File {file} raised the error:\n{ex}")
            return False
    else:
        return False

    # Save tables as a JSON file
    if tables:
        if not Path(output_path).exists():
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(f"{output_path}_tables.json", "w+", encoding="utf-8") as f_out:
            json.dump(get_tables_bioc(tables, Path(file).name), f_out)

    # Save paragraphs as a JSON file
    if paragraphs:
        paragraphs = [x for x in paragraphs if x[0]]
        if not Path(output_path).exists():
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        global args
        with open(f"{output_path}_bioc.json", "w+", encoding="utf-8") as f_out:
            # TODO: Test if datatype causes a problem
            text = get_text_bioc(paragraphs, Path(file).name)
            if args.sentence_splitter:
                text = apply_sentence_splitting(text)
            json.dump(text, f_out, indent=4)

    if not paragraphs and not tables:
        return False
    else:
        return True


def process_directories(input_directory):
    """Processes Word documents in the specified input directory.

    Args:
        input_directory (str): The path to the input directory containing the Word documents.

    Returns:
        None

    Example:
        input_directory = "/path/to/documents"
        process_directories(input_directory)
    """
    global filename
    # Iterate over the files in the input directory and its subdirectories
    for parent, folders_in_parent, files_in_parent in os.walk(input_directory):
        for file in files_in_parent:
            # Check if the file has a ".doc" or ".docx" extension
            if file.endswith(".doc") or file.endswith(".docx"):
                filename = file
                # Process the Word document
                process_word_document(join(parent, file))
