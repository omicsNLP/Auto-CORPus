"""Auto-CORPus primary functions are called from this script, after initialisation with __main__.py."""

import json
from pathlib import Path

from bioc import biocjson, biocxml
from bs4 import BeautifulSoup

from . import logger
from .abbreviation import Abbreviations
from .bioc_formatter import BiocFormatter
from .section import Section
from .table import Table
from .utils import handle_not_tables


class Autocorpus:
    """Parent class for all Auto-CORPus functionality."""

    @staticmethod
    def read_config(config_path: str) -> dict:
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
            return None

        responses = handle_not_tables(config["keywords"], soup)
        if not responses:
            return None

        responses = " ".join(x["node"].get_text() for x in responses)
        return {
            "section_heading": "keywords",
            "subsection_heading": "",
            "body": responses,
            "section_type": [{"iao_name": "keywords section", "iao_id": "IAO:0000630"}],
        }

    def __get_title(self, soup, config):
        if "title" in config:
            titles = handle_not_tables(config["title"], soup)
            if len(titles) == 0:
                return ""
            else:
                return titles[0]["node"].get_text()
        else:
            return ""

    def __get_sections(self, soup, config):
        if "sections" in config:
            sections = handle_not_tables(config["sections"], soup)
            return sections
        return []

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
            maintext.extend(Section(config, sec).to_list())

        # filter out the sections which do not contain any info
        filtered_text = []
        [filtered_text.append(x) for x in maintext if x]
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

    def __handle_html(self, file_path, config):
        """Handles common HTML processing elements across main_text and linked_tables (creates soup and parses tables).

        Args:
            file_path (str): path to the main text file
            config (dict): dict of the maintext
        Return:
            (bs4.BeautifulSoup): soup object
        """
        soup = self.__soupify_infile(file_path)
        if "tables" in config:
            if self.tables == {}:
                self.tables, self.empty_tables = Table(
                    soup, config, file_path, self.base_dir
                ).to_dict()
            else:
                seen_ids = set()
                for tab in self.tables["documents"]:
                    if "." in tab["id"]:
                        seen_ids.add(tab["id"].split(".")[0])
                    else:
                        seen_ids.add(tab["id"])
                tmp_tables, tmp_empty = Table(
                    soup, config, file_path, self.base_dir
                ).to_dict()
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
        return soup

    def __merge_table_data(self):
        if self.empty_tables == []:
            return
        if "documents" in self.tables:
            if self.tables["documents"] == []:
                return
            else:
                seen_ids = {}
                for i, table in enumerate(self.tables["documents"]):
                    if "id" in table:
                        seen_ids[str(i)] = f"Table {table['id']}."
                for table in self.empty_tables:
                    for seenID in seen_ids.keys():
                        if table["title"].startswith(seen_ids[seenID]):
                            if "title" in table and not table["title"] == "":
                                set_new = False
                                for passage in self.tables["documents"][int(seenID)][
                                    "passages"
                                ]:
                                    if (
                                        passage["infons"]["section_type"][0][
                                            "section_name"
                                        ]
                                        == "table_title"
                                    ):
                                        passage["text"] = table["title"]
                                        set_new = True
                                if not set_new:
                                    self.tables["documents"][int(seenID)][
                                        "passages"
                                    ].append(
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
                                pass
                            if "caption" in table and not table["caption"] == "":
                                set_new = False
                                for passage in self.tables["documents"][int(seenID)][
                                    "passages"
                                ]:
                                    if (
                                        passage["infons"]["section_type"][0][
                                            "section_name"
                                        ]
                                        == "table_caption"
                                    ):
                                        passage["text"] = table["caption"]
                                        set_new = True
                                if not set_new:
                                    self.tables["documents"][int(seenID)][
                                        "passages"
                                    ].append(
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
                                pass
                            if "footer" in table and not table["footer"] == "":
                                set_new = False
                                for passage in self.tables["documents"][int(seenID)][
                                    "passages"
                                ]:
                                    if (
                                        passage["infons"]["section_type"][0][
                                            "section_name"
                                        ]
                                        == "table_footer"
                                    ):
                                        passage["text"] = table["footer"]
                                        set_new = True
                                if not set_new:
                                    self.tables["documents"][int(seenID)][
                                        "passages"
                                    ].append(
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
        else:
            return

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
            soup = self.__handle_html(self.file_path, self.config)
            self.main_text = self.__extract_text(soup, self.config)
            try:
                self.abbreviations = Abbreviations(
                    self.main_text, soup, self.config, self.file_path
                ).to_dict()
            except Exception as e:
                logger.error(e)
        if self.linked_tables:
            for table_file in self.linked_tables:
                soup = self.__handle_html(table_file, self.config)
        self.__merge_table_data()
        if "documents" in self.tables and not self.tables["documents"] == []:
            self.has_tables = True

    def __init__(
        self,
        config,
        base_dir=None,
        main_text=None,
        linked_tables=None,
        trained_data=None,
    ):
        """Utilises the input config file to create valid BioC versions of input HTML journal articles.

        Args:
            config (dict): configuration file for the input HTML journal articles
            base_dir (str): base directory of the input HTML journal articles
            main_text (str): path to the main text of the article (HTML files only)
            linked_tables (list): list of linked table file paths to be included in this run (HTML files only)
            trained_data (list): currently unused
        """
        self.base_dir = base_dir
        self.file_path = main_text
        self.linked_tables = linked_tables
        self.config = config
        self.trained_data = trained_data
        self.main_text = {}
        self.empty_tables = {}
        self.tables = {}
        self.abbreviations = {}
        self.has_tables = False

    def to_bioc(self):
        """Get the currently loaded bioc as a dict.

        Returns:
            (dict): bioc as a dict
        """
        return BiocFormatter(self).to_dict()

    def main_text_to_bioc_json(self, indent=2):
        """Get the currently loaded main text as BioC JSON.

        Args:
            indent (int): level of indentation

        Returns:
            (str): main text as BioC JSON
        """
        return BiocFormatter(self).to_json(indent)

    def main_text_to_bioc_xml(self):
        """Get the currently loaded main text as BioC XML.

        Returns:
            (str): main text as BioC XML
        """
        collection = biocjson.loads(BiocFormatter(self).to_json(2))
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
