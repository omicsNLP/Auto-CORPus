"""Auto-CORPus primary functions are defined in this module."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from bs4 import BeautifulSoup, Tag

from . import logger
from .abbreviation import get_abbreviations
from .ac_bioc import BioCJSON, BioCXML
from .bioc_formatter import get_formatted_bioc_collection
from .data_structures import Paragraph
from .section import get_section
from .table import get_table_json
from .utils import handle_not_tables


def soupify_infile(fpath: Path) -> BeautifulSoup:
    """Convert the input file into a BeautifulSoup object.

    Args:
        fpath: Path to the input file.

    Returns:
        BeautifulSoup object of the input file.
    """
    with fpath.open(encoding="utf-8") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
        for e in soup.find_all(attrs={"style": ["display:none", "visibility:hidden"]}):
            e.extract()
        return soup


def get_keywords(soup: BeautifulSoup, config: dict[str, Any]) -> None | Paragraph:
    """Extract keywords from the soup object based on the provided configuration.

    Args:
        soup: BeautifulSoup object of the HTML file.
        config: AC config rules.

    Returns:
        dict: Extracted keywords as a dictionary.
    """
    if "keywords" not in config:
        return None

    responses = handle_not_tables(config["keywords"], soup)
    if not responses:
        return None

    return Paragraph(
        section_heading="keywords",
        subsection_heading="",
        body=" ".join(
            x["node"].get_text() for x in responses if isinstance(x["node"], Tag)
        ),
        section_type=[{"iao_name": "keywords section", "iao_id": "IAO:0000630"}],
    )


def get_title(soup: BeautifulSoup, config: dict[str, Any]) -> str:
    """Extract the title from the soup object based on the provided configuration.

    Args:
        soup: BeautifulSoup object of the HTML file.
        config: AC config rules.

    Returns:
        Extracted title as a string.
    """
    if "title" not in config:
        return ""

    titles = handle_not_tables(config["title"], soup)
    if not titles:
        return ""

    node = cast(Tag, titles[0]["node"])

    return node.get_text()


def get_sections(
    soup: BeautifulSoup, config: dict[str, Any]
) -> list[dict[str, Tag | list[str]]]:
    """Extract sections from the soup object based on the provided configuration.

    Args:
        soup: Beautiful Soup object of the HTML file.
        config: AC config rules.

    Returns:
        A list of matches for the provided config rules. Either as a Tag or a list of
            strings.
    """
    if "sections" not in config:
        return []

    return handle_not_tables(config["sections"], soup)


def set_unknown_section_headings(unique_text: list[Paragraph]) -> list[Paragraph]:
    """Set the heading for sections that are not specified in the config.

    Args:
        unique_text: List of unique text sections.

    Returns:
        A list of unique text sections with unknown headings set to "document part".
    """
    paper = {}
    for para in unique_text:
        if para.section_heading != "keywords":
            paper[para.section_heading] = [x["iao_name"] for x in para.section_type]

    for text in unique_text:
        if not text.section_heading:
            text.section_heading = "document part"
            text.section_type = [{"iao_name": "document part", "iao_id": "IAO:0000314"}]

    return unique_text


def extract_text(soup: BeautifulSoup, config: dict[str, Any]) -> dict[str, Any]:
    """Convert BeautifulSoup object into a Python dict with cleaned main text body.

    Args:
        soup: BeautifulSoup object of html
        config: AC config rules

    Return:
        dict of the maintext
    """
    result: dict[str, Any] = {}

    # Extract tags of text body and hard-code as:
    # p (main text) and span (keywords and refs)
    result["title"] = get_title(soup, config)
    maintext = []
    if keywords := get_keywords(soup, config):
        maintext.append(keywords)
    sections = get_sections(soup, config)
    for sec in sections:
        maintext.extend(get_section(config, sec))

    # filter out the sections which do not contain any info
    filtered_text = [x for x in maintext if x]
    unique_text = []
    seen_text = []
    for text in filtered_text:
        if text.body not in seen_text:
            seen_text.append(text.body)
            unique_text.append(text)

    result["paragraphs"] = [
        p.as_dict() for p in set_unknown_section_headings(unique_text)
    ]

    return result


class Autocorpus:
    """Parent class for all Auto-CORPus functionality."""

    def _extract_soup_and_tables(self, file_path: Path) -> BeautifulSoup:
        """Extract the soup from the html file and assign tables to self.tables.

        Args:
            file_path: The html file path to be processed.

        Returns:
            The BeautifulSoup object of the html file.
        """
        soup = soupify_infile(file_path)
        if "tables" in self.config:
            tables, empty_tables = get_table_json(soup, self.config, file_path)
            self._update_table_ids(tables, empty_tables)
        return soup

    def _update_table_ids(
        self, tables: dict[str, Any], empty_tables: list[dict[str, Any]]
    ):
        """Update the table IDs in the new tables to avoid conflicts with existing ones.

        Args:
            tables: New tables dictionary to be updated in line with self.tables.
            empty_tables: New empty tables list to add to self.empty_tables.
        """
        if not self.tables:
            self.tables: dict[str, Any] = tables
            self.empty_tables = empty_tables
            return

        seen_ids = set()
        for tab in self.tables["documents"]:
            if "." in tab["id"]:
                seen_ids.add(tab["id"].split(".")[0])
            else:
                seen_ids.add(tab["id"])

        for tabl in tables["documents"]:
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

        self.tables["documents"].extend(tables["documents"])
        self.empty_tables.extend(empty_tables)

    def _merge_table_data(self):
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

    def _extract_html_article(self, file_path: Path):
        soup = self._extract_soup_and_tables(file_path)
        self.main_text = extract_text(soup, self.config)
        try:
            self.abbreviations = get_abbreviations(self.main_text, soup, file_path)
        except Exception as e:
            logger.error(e)

    def process_html_article(self):
        """Processes the main text file and tables specified in the configuration.

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
        5. Checks if there are any documents in the tables and sets the `has_tables`
            attribute accordingly.

        Raises:
            RuntimeError: If no valid configuration is loaded.
        """
        if not self.config:
            raise RuntimeError("A valid config file must be loaded.")

        self._extract_html_article(self.file_path)
        for table_file in self.linked_tables:
            self._extract_soup_and_tables(table_file)
        self._merge_table_data()
        self.has_tables = bool(self.tables.get("documents"))

    def _process_file(self):
        """Process the input file based on its type.

        This method checks the file extension and processes the file accordingly.

        Raises:
            NotImplementedError: _description_
        """
        match self.file_path.suffix:
            case ".html" | ".htm":
                self.process_html_article()
            case ".xml":
                raise NotImplementedError("XML processing is not implemented yet.")
            case ".pdf":
                try:
                    from .ac_bioc.json import BioCJSONEncoder
                    from .pdf import extract_pdf_content

                    text, tables = extract_pdf_content(self.file_path)

                    # TODO: Use text.to_dict() after bugfix in ac_bioc
                    self.main_text = BioCJSONEncoder().default(text)
                    self.tables = BioCJSONEncoder().default(tables)

                except ModuleNotFoundError:
                    logger.error(
                        "Could not load necessary PDF packages. If you installed "
                        "Auto-CORPUS via pip, you can obtain these with:\n"
                        "    pip install autocorpus[pdf]"
                    )
                    raise
            case _:
                pass

    def __init__(
        self,
        config: dict[str, Any],
        file_path: Path,
        linked_tables: list[Path] = [],
    ):
        """Create valid BioC versions of input HTML journal articles based off config.

        Args:
            config: Configuration dictionary for the input journal articles
            file_path: Path to the article file to be processed
            linked_tables: list of linked table file paths to be included in this run
                (HTML files only)
        """
        self.file_path = file_path
        self.linked_tables = linked_tables
        self.config = config
        self.main_text = {}
        self.empty_tables = []
        self.tables = {}
        self.abbreviations = {}
        self.has_tables = False

        self._process_file()

    def to_bioc(self) -> dict[str, Any]:
        """Get the currently loaded bioc as a dict.

        Returns:
            bioc as a dict
        """
        return get_formatted_bioc_collection(self.main_text, self.file_path)

    def main_text_to_bioc_json(self) -> str:
        """Get the currently loaded main text as BioC JSON.

        Args:
            indent: level of indentation

        Returns:
            main text as BioC JSON
        """
        return json.dumps(
            get_formatted_bioc_collection(self.main_text, self.file_path),
            indent=2,
            ensure_ascii=False,
        )

    def main_text_to_bioc_xml(self) -> str:
        """Get the currently loaded main text as BioC XML.

        Returns:
            main text as BioC XML
        """
        collection = BioCJSON.loads(
            json.dumps(
                get_formatted_bioc_collection(self.main_text, self.file_path),
                indent=2,
                ensure_ascii=False,
            )
        )
        return BioCXML.dumps(collection)

    def tables_to_bioc_json(self, indent: int = 2) -> str:
        """Get the currently loaded tables as Tables-JSON.

        Args:
            indent: level of indentation

        Returns:
            tables as Tables-JSON
        """
        return json.dumps(self.tables, ensure_ascii=False, indent=indent)

    def abbreviations_to_bioc_json(self, indent: int = 2) -> str:
        """Get the currently loaded abbreviations as BioC JSON.

        Args:
            indent: level of indentation

        Returns:
            abbreviations as BioC JSON
        """
        return json.dumps(self.abbreviations, ensure_ascii=False, indent=indent)

    def to_json(self, indent: int = 2) -> str:
        """Get the currently loaded AC object as a dict.

        Args:
            indent: Level of indentation.

        Returns:
            AC object as a JSON string
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_dict(self) -> dict[str, Any]:
        """Get the currently loaded AC object as a dict.

        Returns:
            AC object as a dict
        """
        return {
            "main_text": self.main_text,
            "abbreviations": self.abbreviations,
            "tables": self.tables,
        }


def process_directory(config: dict[str, Any], dir_path: Path) -> Iterable[Autocorpus]:
    """Process all files in a directory and its subdirectories.

    Args:
        config: Configuration dictionary for the input HTML journal articles
        dir_path: Path to the directory containing files to be processed.

    Returns:
        A generator yielding Autocorpus objects for each processed file.
    """
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            yield Autocorpus(config, file_path)

        elif file_path.is_dir():
            # recursively process all files in the subdirectory
            for sub_file_path in file_path.rglob("*"):
                yield Autocorpus(config, sub_file_path)


def process_files(config: dict[str, Any], files: list[Path]) -> Iterable[Autocorpus]:
    """Process all files in a list.

    Args:
        config: Configuration dictionary for the input HTML journal articles
        files: list of Paths to the files to be processed.

    Returns:
        A generator yielding Autocorpus objects for each processed file.

    Raises:
        RuntimeError: If the list of files is invalid.
    """
    if not all(file.is_file() for file in files):
        raise RuntimeError("All files must be valid file paths.")

    for file_path in files:
        yield Autocorpus(config, file_path)
