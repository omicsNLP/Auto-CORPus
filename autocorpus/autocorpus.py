"""Auto-CORPus primary functions are called from this script, after initialisation with __main__.py."""

import json
from pathlib import Path
from typing import Any

from bioc import biocjson, biocxml
from bs4 import BeautifulSoup
from marker.converters.pdf import PdfConverter  # type: ignore
from marker.models import create_model_dict  # type: ignore
from marker.output import text_from_rendered  # type: ignore

from autocorpus.bioc_supplementary import (
    BioCTableConverter,
    BioCTextConverter,
    extract_table_from_pdf_text,
)

from . import logger
from .abbreviation import Abbreviations
from .bioc_formatter import get_formatted_bioc_collection
from .section import get_section
from .table import get_table_json
from .utils import handle_not_tables

pdf_converter: PdfConverter | None = None


def __load_pdf_models():
    global pdf_converter
    if pdf_converter is None:
        pdf_converter = PdfConverter(
            artifact_dict=create_model_dict(),
        )


class Autocorpus:
    """Parent class for all Auto-CORPus functionality."""

    @staticmethod
    def read_config(config_path: str) -> dict[str, Any]:
        """Reads a configuration file and returns its content.

        Args:
            config_path (str): The path to the configuration file.

        Returns:
            dict: The content of the configuration file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the configuration file is not a valid JSON.
            KeyError: If the configuration file does not contain the expected "config" key.
        """
        with open(config_path, encoding="utf-8") as f:
            ## TODO: validate config file here if possible
            content = json.load(f)
            return content["config"]

    def __soupify_infile(self, fpath):
        fpath = Path(fpath)
        with fpath.open(encoding="utf-8") as fp:
            soup = BeautifulSoup(fp.read(), "html.parser")
            for e in soup.find_all(
                attrs={"style": ["display:none", "visibility:hidden"]}
            ):
                e.extract()
            return soup

    def __get_keywords(self, soup, config):
        if "keywords" not in config:
            return {}

        responses = handle_not_tables(config["keywords"], soup)
        if not responses:
            return {}

        responses = " ".join(x["node"].get_text() for x in responses)
        return {
            "section_heading": "keywords",
            "subsection_heading": "",
            "body": responses,
            "section_type": [{"iao_name": "keywords section", "iao_id": "IAO:0000630"}],
        }

    def __get_title(self, soup, config):
        if "title" not in config:
            return ""

        titles = handle_not_tables(config["title"], soup)
        if not titles:
            return ""

        return titles[0]["node"].get_text()

    def __get_sections(self, soup, config):
        if "sections" not in config:
            return []

        return handle_not_tables(config["sections"], soup)

    @staticmethod
    def __extract_pdf_content(
        file_path: Path,
    ) -> bool:
        """Extracts content from a PDF file.

        Args:
            file_path (Path): Path to the PDF file.

        Returns:
            bool: success status of the extraction process.
        """
        bioc_text, bioc_tables = None, None

        __load_pdf_models()
        if pdf_converter:
            # extract text from PDF
            rendered = pdf_converter(file_path)
            text, _, _ = text_from_rendered(rendered)
            # seperate text and tables
            text, tables = extract_table_from_pdf_text(text)
            # format data for BioC
            bioc_text = BioCTextConverter(text, "pdf")
            bioc_text.output_bioc_json(file_path)
            bioc_tables = BioCTableConverter(tables)
            bioc_tables.output_tables_json(file_path)
            return True
        else:
            logger.error("PDF converter not initialized.")
            return False

    def __extract_text(self, soup, config):
        """Convert beautiful soup object into a python dict object with cleaned main text body.

        Args:
            soup (bs4.BeautifulSoup): BeautifulSoup object of html
            config (dict): AC config rules

        Return:
            (dict): dict of the maintext
        """
        result = {}

        # Tags of text body to be extracted are hard-coded as p (main text) and span (keywords and refs)
        result["title"] = self.__get_title(soup, config)
        maintext = []
        if keywords := self.__get_keywords(soup, config):
            maintext.append(keywords)
        sections = self.__get_sections(soup, config)
        for sec in sections:
            maintext.extend(get_section(config, sec))

        # filter out the sections which do not contain any info
        filtered_text = [x for x in maintext if x]
        unique_text = []
        seen_text = []
        for text in filtered_text:
            if text["body"] not in seen_text:
                seen_text.append(text["body"])
                unique_text.append(text)

        result["paragraphs"] = self.__set_unknown_section_headings(unique_text)

        return result

    def __set_unknown_section_headings(self, unique_text):
        paper = {}
        for para in unique_text:
            if para["section_heading"] != "keywords":
                paper[para["section_heading"]] = [
                    x["iao_name"] for x in para["section_type"]
                ]

        for text in unique_text:
            if not text["section_heading"]:
                text["section_heading"] = "document part"
                text["section_type"] = [
                    {"iao_name": "document part", "iao_id": "IAO:0000314"}
                ]

        return unique_text

    def __process_html_tables(self, file_path, soup, config):
        """Extract data from tables in the HTML file.

        Args:
            file_path (str): path to the main text file
            soup (bs4.BeautifulSoup): soup object
            config (dict): dict of the maintext
        """
        if "tables" not in config:
            return

        if not self.tables:
            self.tables, self.empty_tables = get_table_json(soup, config, file_path)
            return

        seen_ids = set()
        for tab in self.tables["documents"]:
            if "." in tab["id"]:
                seen_ids.add(tab["id"].split(".")[0])
            else:
                seen_ids.add(tab["id"])

        tmp_tables, tmp_empty = get_table_json(soup, config, file_path)
        for tabl in tmp_tables["documents"]:
            if "." in tabl["id"]:
                tabl_id = tabl["id"].split(".")[0]
                tabl_pos = ".".join(tabl["id"].split(".")[1:])
            else:
                tabl_id = tabl["id"]
                tabl_pos = None
            if tabl_id in seen_ids:
                tabl_id = str(len(seen_ids) + 1)
                if tabl_pos:
                    tabl["id"] = f"{tabl_id}.{tabl_pos}"
                else:
                    tabl["id"] = tabl_id
            seen_ids.add(tabl_id)
        self.tables["documents"].extend(tmp_tables["documents"])
        self.empty_tables.extend(tmp_empty)

    def __merge_table_data(self):
        if not self.empty_tables:
            return

        documents = self.tables.get("documents", None)
        if not documents:
            return

        seen_ids = {}
        for i, table in enumerate(documents):
            if "id" in table:
                seen_ids[str(i)] = f"Table {table['id']}."

        for table in self.empty_tables:
            for seenID in seen_ids.keys():
                if not table["title"].startswith(seen_ids[seenID]):
                    continue

                if "title" in table and not table["title"] == "":
                    set_new = False
                    for passage in documents[int(seenID)]["passages"]:
                        if (
                            passage["infons"]["section_type"][0]["section_name"]
                            == "table_title"
                        ):
                            passage["text"] = table["title"]
                            set_new = True
                    if not set_new:
                        documents[int(seenID)]["passages"].append(
                            {
                                "offset": 0,
                                "infons": {
                                    "section_type": [
                                        {
                                            "section_name": "table_title",
                                            "iao_name": "document title",
                                            "iao_id": "IAO:0000305",
                                        }
                                    ]
                                },
                                "text": table["title"],
                            }
                        )
                if "caption" in table and not table["caption"] == "":
                    set_new = False
                    for passage in documents[int(seenID)]["passages"]:
                        if (
                            passage["infons"]["section_type"][0]["section_name"]
                            == "table_caption"
                        ):
                            passage["text"] = table["caption"]
                            set_new = True
                    if not set_new:
                        documents[int(seenID)]["passages"].append(
                            {
                                "offset": 0,
                                "infons": {
                                    "section_type": [
                                        {
                                            "section_name": "table_caption",
                                            "iao_name": "caption",
                                            "iao_id": "IAO:0000304",
                                        }
                                    ]
                                },
                                "text": table["caption"],
                            }
                        )
                if "footer" in table and not table["footer"] == "":
                    set_new = False
                    for passage in documents[int(seenID)]["passages"]:
                        if (
                            passage["infons"]["section_type"][0]["section_name"]
                            == "table_footer"
                        ):
                            passage["text"] = table["footer"]
                            set_new = True
                    if not set_new:
                        documents[int(seenID)]["passages"].append(
                            {
                                "offset": 0,
                                "infons": {
                                    "section_type": [
                                        {
                                            "section_name": "table_footer",
                                            "iao_name": "caption",
                                            "iao_id": "IAO:0000304",
                                        }
                                    ]
                                },
                                "text": table["footer"],
                            }
                        )

    def process_files(self):
        """Processes the files specified in the configuration.

        This method performs the following steps:
        1. Checks if a valid configuration is loaded. If not, raises a RuntimeError.
        2. Handles the main text file:
            - Parses the HTML content of the file.
            - Extracts the main text from the parsed HTML.
            - Attempts to extract abbreviations from the main text and HTML content.
              If an error occurs during this process, it prints the error.
        3. Processes linked tables, if any:
            - Parses the HTML content of each linked table file.
        4. Merges table data.
        5. Checks if there are any documents in the tables and sets the `has_tables` attribute accordingly.

        Raises:
            RuntimeError: If no valid configuration is loaded.
        """
        if not self.config:
            raise RuntimeError("A valid config file must be loaded.")
        # handle main_text
        if self.file_path:
            soup = self.__soupify_infile(self.file_path)
            self.__process_html_tables(self.file_path, soup, self.config)
            self.main_text = self.__extract_text(soup, self.config)
            try:
                self.abbreviations = Abbreviations(
                    self.main_text, soup, self.config, self.file_path
                ).to_dict()
            except Exception as e:
                logger.error(e)
            # check and process files nested in folders as supplementary files.
            input_path = Path(self.file_path)
            if input_path.is_dir():
                # check if the provided directory contains subdirectories
                for file in input_path.iterdir():
                    # ignore files at this level, they are already processed as main text.
                    if file.is_dir():
                        # recursively process all files in the subdirectory
                        # rglob should filter for only processable file extensions.
                        for sub_file in file.rglob(".pdf"):
                            if sub_file.suffix == ".pdf":
                                bioc_text, bioc_tables = self.__extract_pdf_content(
                                    sub_file
                                )

        if self.linked_tables:
            for table_file in self.linked_tables:
                soup = self.__soupify_infile(table_file)
                self.__process_html_tables(table_file, soup, self.config)
        self.__merge_table_data()
        if "documents" in self.tables and not self.tables["documents"] == []:
            self.has_tables = True

    def __init__(
        self,
        config: dict[str, Any],
        main_text: Path,
        linked_tables=None,
    ):
        """Utilises the input config file to create valid BioC versions of input HTML journal articles.

        Args:
            config (dict): configuration file for the input HTML journal articles
            main_text (Path): path to the main text of the article (HTML files only)
            linked_tables (list): list of linked table file paths to be included in this run (HTML files only)
        """
        self.file_path = main_text
        self.linked_tables = linked_tables
        self.config = config
        self.main_text = {}
        self.empty_tables = []
        self.tables = {}
        self.abbreviations = {}
        self.has_tables = False

    def to_bioc(self):
        """Get the currently loaded bioc as a dict.

        Returns:
            (dict): bioc as a dict
        """
        return get_formatted_bioc_collection(self)

    def main_text_to_bioc_json(self):
        """Get the currently loaded main text as BioC JSON.

        Args:
            indent (int): level of indentation

        Returns:
            (str): main text as BioC JSON
        """
        return json.dumps(
            get_formatted_bioc_collection(self), indent=2, ensure_ascii=False
        )

    def main_text_to_bioc_xml(self):
        """Get the currently loaded main text as BioC XML.

        Returns:
            (str): main text as BioC XML
        """
        collection = biocjson.loads(
            json.dumps(
                get_formatted_bioc_collection(self), indent=2, ensure_ascii=False
            )
        )
        return biocxml.dumps(collection)

    def tables_to_bioc_json(self, indent=2):
        """Get the currently loaded tables as Tables-JSON.

        Args:
            indent (int): level of indentation

        Returns:
            (str): tables as Tables-JSON
        """
        return json.dumps(self.tables, ensure_ascii=False, indent=indent)

    def abbreviations_to_bioc_json(self, indent=2):
        """Get the currently loaded abbreviations as BioC JSON.

        Args:
            indent (int): level of indentation

        Returns:
            (str): abbreviations as BioC JSON
        """
        return json.dumps(self.abbreviations, ensure_ascii=False, indent=indent)

    def to_json(self, indent=2):
        """Get the currently loaded AC object as a dict.

        Args:
            indent (int): Level of indentation.

        Returns:
            (str): AC object as a JSON string
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_dict(self):
        """Get the currently loaded AC object as a dict.

        Returns:
            (dict): AC object as a dict
        """
        return {
            "main_text": self.main_text,
            "abbreviations": self.abbreviations,
            "tables": self.tables,
        }
