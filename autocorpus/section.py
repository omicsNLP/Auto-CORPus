"""Handles section processing for Auto-CORPus.

Modules used:
- re: regular expression searching/replacing.
- nltk: string tokenization
- fuzzywuzzy: string-in-string ratio
"""

import re
from functools import lru_cache
from importlib import resources
from typing import Any

import nltk
from fuzzywuzzy import fuzz

from . import logger
from .references import get_reference
from .utils import handle_not_tables


@lru_cache
def read_mapping_file() -> dict[str, list[str]]:
    """Reads the IAO mapping file and parses it into a dictionary.

    Returns:
        The parsed IAO mappings
    """
    mapping_dict: dict[str, list[str]] = {}
    mapping_path = resources.files("autocorpus.IAO_dicts") / "IAO_FINAL_MAPPING.txt"
    with mapping_path.open(encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            heading, _, iao_term = line.rstrip("\n").lower().partition("\t")
            if iao_term != "":
                if "/" in iao_term:
                    iao_term_1 = iao_term.split("/")[0].strip(" ")
                    iao_term_2 = iao_term.split("/")[1].strip(" ")
                    if iao_term_1 in mapping_dict.keys():
                        mapping_dict[iao_term_1].append(heading)
                    else:
                        mapping_dict.update({iao_term_1: [heading]})

                    if iao_term_2 in mapping_dict.keys():
                        mapping_dict[iao_term_2].append(heading)
                    else:
                        mapping_dict.update({iao_term_2: [heading]})

                else:
                    if iao_term in mapping_dict.keys():
                        mapping_dict[iao_term].append(heading)
                    else:
                        mapping_dict.update({iao_term: [heading]})
    return mapping_dict


@lru_cache
def read_iao_term_to_id_file() -> dict[str, str]:
    """Parses the IAO_term_to_ID.txt file.

    Returns:
        Parsed IAO ids as a dictionary
    """
    iao_term_to_no_dict = {}
    id_path = resources.files("autocorpus.IAO_dicts") / "IAO_term_to_ID.txt"
    with id_path.open(encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            iao_term, _, iao_no = line.rstrip("\n").partition("\t")
            iao_term_to_no_dict.update({iao_term: iao_no})
    return iao_term_to_no_dict


def get_iao_term_mapping(section_heading: str) -> list[dict[str, str]]:
    """Get the IAO term mapping for a given section heading.

    Args:
        section_heading: The name of the section heading.

    Returns:
        The IAO term mapping for the section heading.
    """
    mapping_dict = read_mapping_file()
    tokenized_section_heading = nltk.wordpunct_tokenize(section_heading)
    text = nltk.Text(tokenized_section_heading)
    words = [w.lower() for w in text]
    h2_tmp = " ".join(word for word in words)

    # TODO: check for best match, not the first
    mapping_result = []
    if h2_tmp != "":
        if any(x in h2_tmp for x in [" and ", "&", "/"]):
            h2_parts = re.split(r" and |\s?/\s?|\s?&\s?", h2_tmp)
            for h2_part in h2_parts:
                h2_part = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_part)
                for IAO_term, heading_list in mapping_dict.items():
                    if any(
                        fuzz.ratio(h2_part, heading) >= 80 for heading in heading_list
                    ):
                        mapping_result.append(get_iao_term_to_id_mapping(IAO_term))
                        break

        else:
            for IAO_term, heading_list in mapping_dict.items():
                h2_tmp = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_tmp)
                if any([fuzz.ratio(h2_tmp, heading) > 80 for heading in heading_list]):
                    mapping_result = [get_iao_term_to_id_mapping(IAO_term)]
                    break

    if mapping_result == []:
        return [{"iao_name": "document part", "iao_id": "IAO:0000314"}]

    return mapping_result


def get_iao_term_to_id_mapping(iao_term: str) -> dict[str, str]:
    """Map IAO terms to IAO IDs.

    Args:
        iao_term: IAO term to map to an IAO ID.

    Returns:
        A dictionary containing the IAO term and its corresponding ID
    """
    mapping_result_id_version = read_iao_term_to_id_file().get(iao_term, "")

    return {"iao_name": iao_term, "iao_id": mapping_result_id_version}


class Section:
    """Class for processing section data."""

    def __add_paragraph(self, body):
        self.paragraphs.append(
            {
                "section_heading": self.section_heading,
                "subsection_heading": self.subheader,
                "body": body,
                "section_type": self.section_type,
            }
        )

    def __navigate_children(self, soup_section, all_sub_sections, filtered_paragraphs):
        if soup_section in filtered_paragraphs:
            if soup_section.previous_sibling and soup_section.previous_sibling.name in (
                "h3",
                "h4",
                "h5",
            ):
                self.subheader = soup_section.previous_sibling.get_text()
            self.__add_paragraph(soup_section.get_text())
            return
        for subsec in all_sub_sections:
            if subsec["node"] == soup_section:
                self.subheader = (
                    subsec["headers"][0]
                    if "headers" in subsec and not subsec["headers"] == ""
                    else ""
                )

        try:
            children = soup_section.findChildren(recursive=False)
        except Exception as e:
            logger.warning(e)
            children = []
        for child in children:
            self.__navigate_children(child, all_sub_sections, filtered_paragraphs)

    def __get_abbreviations(self, soup_section):
        if "abbreviations-table" in self.config:
            try:
                abbreviations_tables = handle_not_tables(
                    self.config["abbreviations-table"], soup_section
                )
                abbreviations_tables = abbreviations_tables[0]["node"]
                abbreviations = {}
                for tr in abbreviations_tables.find_all("tr"):
                    short_form, long_form = (td.get_text() for td in tr.find_all("td"))
                    abbreviations[short_form] = long_form
            except Exception:
                abbreviations = {}
            self.__add_paragraph(str(abbreviations))

    def __get_section(self, soup_section):
        all_sub_sections = handle_not_tables(self.config["sub-sections"], soup_section)
        all_paragraphs = handle_not_tables(self.config["paragraphs"], soup_section)
        all_paragraphs = [x["node"] for x in all_paragraphs]
        all_tables = handle_not_tables(self.config["tables"], soup_section)
        all_tables = [x["node"] for x in all_tables]
        all_figures = handle_not_tables(self.config["figures"], soup_section)
        all_figures = [x["node"] for x in all_figures]
        unwanted_paragraphs = []
        [
            unwanted_paragraphs.extend(capt.find_all("p", recursive=True))
            for capt in all_tables
        ]
        [
            unwanted_paragraphs.extend(capt.find_all("p", recursive=True))
            for capt in all_figures
        ]
        all_paragraphs = [
            para for para in all_paragraphs if para not in unwanted_paragraphs
        ]
        children = soup_section.findChildren(recursive=False)
        for child in children:
            self.__navigate_children(child, all_sub_sections, all_paragraphs)

    def __get_references(self, soup_section):
        """Constructs the article references using the provided configuration file.

        Args:
            soup_section (bs4.BeautifulSoup): article section containing references
        """
        all_references = handle_not_tables(self.config["references"], soup_section)
        for ref in all_references:
            self.paragraphs.append(get_reference(ref, self.section_heading))

    def __init__(self, config: dict[str, Any], section_dict: dict[str, Any]) -> None:
        """Identifies a section using the provided configuration.

        Args:
            config: AC configuration object.
            section_dict: Article section dictionary.
        """
        self.config = config
        self.section_heading = section_dict.get("headers", [""])[0]
        self.section_type = get_iao_term_mapping(self.section_heading)
        self.subheader = ""
        self.paragraphs: list[dict[str, str]] = []
        if self.section_heading == "Abbreviations":
            self.__get_abbreviations(section_dict["node"])
        elif {
            "iao_name": "references section",
            "iao_id": "IAO:0000320",
        } in self.section_type:
            self.__get_references(section_dict["node"])
        else:
            self.__get_section(section_dict["node"])

    def to_list(self) -> list[dict[str, str]]:
        """Retrieve a list of section paragraphs.

        Returns:
                The section paragraphs
        """
        return self.paragraphs
