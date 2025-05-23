"""Auto-CORPus primary functions are called from this script, after initialisation with __main__.py."""

import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from . import logger
from .abbreviation import get_abbreviations
from .ac_bioc import BioCJSON, BioCXML
from .bioc_formatter import get_formatted_bioc_collection
from .section import get_section
from .table import get_table_json
from .utils import handle_not_tables


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

    def __soupify_infile(self, fpath: Path):
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

    def __process_html_article(self, file: Path):
        soup = self.__soupify_infile(file)
        self.__process_html_tables(file, soup, self.config)
        self.main_text = self.__extract_text(soup, self.config)
        try:
            self.abbreviations = get_abbreviations(self.main_text, soup, str(file))
        except Exception as e:
            logger.error(e)

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

    def __process_supplementary_file(self, file: Path):
        match file.suffix:
            case ".html" | ".htm":
                self.__process_html_article(file)
            case ".xml":
                pass
            case ".pdf":
                try:
                    from .pdf import extract_pdf_content

                    extract_pdf_content(file)
                except ModuleNotFoundError:
                    logger.error(
                        "Could not load necessary PDF packages. "
                        "If you installed Auto-CORPUS via pip, you can obtain these with:\n"
                        "    pip install autocorpus[pdf]"
                    )
                    raise
            case _:
                pass

    def process_file(self):
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
            soup = self.__soupify_infile(Path(self.file_path))
            self.__process_html_tables(self.file_path, soup, self.config)
            self.main_text = self.__extract_text(soup, self.config)
            try:
                self.abbreviations = get_abbreviations(
                    self.main_text, soup, self.file_path
                )
            except Exception as e:
                logger.error(e)
        if self.linked_tables:
            for table_file in self.linked_tables:
                soup = self.__soupify_infile(table_file)
                self.__process_html_tables(table_file, soup, self.config)
        self.__merge_table_data()
        if "documents" in self.tables and not self.tables["documents"] == []:
            self.has_tables = True

    def process_files(
        self,
        files: list[Path | str] = [],
        dir_path: Path | str = "",
        linked_tables: list[Path | str] = [],
    ):
        """Processes main text files provided and nested supplementary files.

        Raises:
            RuntimeError: If no valid configuration is provided.
        """
        # Either a list of specific files or a directory path must be provided.
        if not (files or dir_path):
            logger.error("No files or directory provided.")
            raise FileNotFoundError("No files or directory provided.")
        #
        if dir_path:
            # Path is the preferred type, users can also provide a string though
            if isinstance(dir_path, str):
                dir_path = Path(dir_path)
            for file in dir_path.iterdir():
                if file.is_file() and file.suffix in [".html", ".htm"]:
                    self.__process_html_article(file)
                elif file.is_dir():
                    # recursively process all files in the subdirectory
                    for sub_file in file.rglob("*"):
                        self.__process_supplementary_file(sub_file)

        # process any specific files provided
        for specific_file in files:
            # Path is the preferred type, users can also provide a string though
            if isinstance(specific_file, str):
                specific_file = Path(specific_file)
            if specific_file.is_file() and specific_file.suffix in [".html", ".htm"]:
                self.__process_html_article(specific_file)
            else:
                # process any specific files provided
                self.__process_supplementary_file(specific_file)

    def __init__(
        self,
        config: dict[str, Any],
        main_text: Path | None = None,
        linked_tables=None,
    ):
        """Utilises the input config file to create valid BioC versions of input HTML journal articles.

        Args:
            config (dict): configuration file for the input HTML journal articles
            main_text (Path): path to the main text of the article (HTML files only)
            linked_tables (list): list of linked table file paths to be included in this run (HTML files only)
        """
        self.file_path = str(main_text)
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
        collection = BioCJSON.loads(
            json.dumps(
                get_formatted_bioc_collection(self), indent=2, ensure_ascii=False
            )
        )
        return BioCXML.dumps(collection)

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
