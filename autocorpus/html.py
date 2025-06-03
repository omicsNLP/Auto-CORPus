"""The Auto-CORPus HTML processing module."""

from pathlib import Path
from typing import Any, cast

from bs4 import BeautifulSoup, Tag

from . import logger
from .abbreviation import get_abbreviations
from .data_structures import Paragraph
from .section import get_section
from .table import get_table_json
from .utils import handle_not_tables


def load_html_file(fpath: Path) -> BeautifulSoup:
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


def _get_keywords(
    soup: BeautifulSoup, keywords_config: dict[str, Any]
) -> Paragraph | None:
    """Extract keywords from the soup object based on the provided configuration.

    Args:
        soup: BeautifulSoup object of the HTML file.
        keywords_config: AC config rules for keywords.

    Returns:
        dict: Extracted keywords as a dictionary.
    """
    responses = handle_not_tables(keywords_config, soup)
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


def _get_title(soup: BeautifulSoup, title_config: dict[str, Any]) -> str:
    """Extract the title from the soup object based on the provided configuration.

    Args:
        soup: BeautifulSoup object of the HTML file.
        title_config: AC config rules for the title.

    Returns:
        Extracted title as a string.
    """
    titles = handle_not_tables(title_config, soup)
    if not titles:
        return ""

    node = cast(Tag, titles[0]["node"])

    return node.get_text()


def _get_sections(
    soup: BeautifulSoup, sections_config: dict[str, Any]
) -> list[dict[str, Tag | list[str]]]:
    """Extract sections from the soup object based on the provided configuration.

    Args:
        soup: Beautiful Soup object of the HTML file.
        sections_config: AC config rules for sections.

    Returns:
        A list of matches for the provided config rules. Either as a Tag or a list of
            strings.
    """
    return handle_not_tables(sections_config, soup)


def _set_unknown_section_headings(unique_text: list[Paragraph]) -> list[Paragraph]:
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


def _extract_text(soup: BeautifulSoup, config: dict[str, Any]) -> dict[str, Any]:
    """Extract the main text of the article from the soup object.

    This converts a BeautifulSoup object of a html article into a Python dict that
    aligns with the BioC format defined in the provided config.

    Args:
        soup: BeautifulSoup object of html
        config: AC config rules

    Return:
        dict of the maintext
    """
    result: dict[str, Any] = {}

    # Extract tags of text body and hard-code as:
    # p (main text) and span (keywords and refs)
    result["title"] = _get_title(soup, config["title"]) if "title" in config else ""
    maintext = []
    if "keywords" in config and (keywords := _get_keywords(soup, config["keywords"])):
        maintext.append(keywords)
    sections = _get_sections(soup, config["sections"]) if "sections" in config else []
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
        p.as_dict() for p in _set_unknown_section_headings(unique_text)
    ]

    return result


def _extend_tables_documents(
    documents: list[dict[str, Any]], new_documents: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Extends the list of tables documents with new documents, ensuring unique IDs.

    Args:
        documents: The original list of documents to be extended.
        new_documents: New list of documents to add.

    Returns:
        A list of documents with unique IDs, combining the original and new documents.
    """
    seen_ids = set()
    for doc in documents:
        seen_ids.add(doc["id"].partition(".")[0])

    for doc in new_documents:
        tabl_id, _, tabl_pos = doc["id"].partition(".")
        if tabl_id in seen_ids:
            tabl_id = str(len(seen_ids) + 1)
            if tabl_pos:
                doc["id"] = f"{tabl_id}.{tabl_pos}"
            else:
                doc["id"] = tabl_id
        seen_ids.add(tabl_id)

    documents.extend(new_documents)

    return documents


def _merge_tables_with_empty_tables(
    documents: list[dict[str, Any]], empty_tables: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Extends the list of tables documents with empty tables, ensuring titles are set.

    Args:
        documents: The original list of documents to be extended.
        empty_tables: A list of empty tables to merge with the documents.

    Returns:
        A list of documents with titles and captions from empty tables merged in.
    """

    def _set_table_passage(passages, section_name, iao_name, iao_id, text):
        set_new = False
        for passage in passages:
            if passage["infons"]["section_type"][0]["section_name"] == section_name:
                passage["text"] = text
                set_new = True
        if set_new:
            return passages
        return {
            "offset": 0,
            "infons": {
                "section_type": [
                    {
                        "section_name": section_name,
                        "iao_name": iao_name,
                        "iao_id": iao_id,
                    }
                ]
            },
            "text": text,
        }

    seen_ids: dict[int, str] = {}
    for i, table in enumerate(documents):
        if "id" in table:
            seen_ids[i] = f"Table {table['id']}."

    for table in empty_tables:
        for seen_id in seen_ids:
            if not table["title"].startswith(seen_ids[seen_id]):
                continue

            if title := table.get("title"):
                documents[seen_id]["passages"] = _set_table_passage(
                    documents[seen_id]["passages"],
                    "table_title",
                    "document title",
                    "IAO:0000305",
                    title,
                )
            if caption := table.get("caption"):
                documents[seen_id]["passages"] = _set_table_passage(
                    documents[seen_id],
                    "table_caption",
                    "caption",
                    "IAO:0000304",
                    caption,
                )
            if footer := table.get("footer"):
                documents[seen_id]["passages"] = _set_table_passage(
                    documents[seen_id],
                    "table_footer",
                    "caption",
                    "IAO:0000304",
                    footer,
                )
    return documents


def process_html_article(
    config: dict[str, Any], file_path: Path, linked_tables: list[Path] = []
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Create valid BioC versions of input HTML journal articles based off config.

    Processes the main text file and tables specified in the configuration.

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

    Args:
        config: Configuration dictionary for the input journal articles
        file_path: Path to the article file to be processed
        linked_tables: list of linked table file paths to be included in this run
            (HTML files only)

    Returns:
        A tuple containing:
            - main_text: Extracted main text as a dictionary.
            - abbreviations: Extracted abbreviations as a dictionary.
            - tables: Extracted tables as a dictionary (possibly empty).

    Raises:
        RuntimeError: If no valid configuration is loaded.
    """
    if config == {}:
        raise RuntimeError("A valid config file must be loaded.")

    soup = load_html_file(file_path)
    main_text = _extract_text(soup, config)
    try:
        abbreviations = get_abbreviations(main_text, soup, file_path)
    except Exception as e:
        logger.error(e)

    if "tables" not in config:
        return main_text, abbreviations, dict()

    tables, empty_tables = get_table_json(soup, config, file_path)

    new_documents = []
    for table_file in linked_tables:
        soup = load_html_file(table_file)
        new_tables, new_empty_tables = get_table_json(soup, config, table_file)
        new_documents.extend(new_tables.get("documents", []))
        empty_tables.extend(new_empty_tables)
    tables["documents"] = _extend_tables_documents(
        tables.get("documents", []), new_documents
    )
    if empty_tables:
        tables["documents"] = _merge_tables_with_empty_tables(
            tables["documents"], empty_tables
        )

    return main_text, abbreviations, tables
