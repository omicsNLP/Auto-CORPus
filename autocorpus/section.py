"""Handles section processing for Auto-CORPus.

Modules used:
- re: regular expression searching/replacing.
- nltk: string tokenization
- fuzzywuzzy: string-in-string ratio
"""

import re

import nltk
from fuzzywuzzy import fuzz

from . import logger
from .references import References
from .utils import handle_not_tables, read_iao_term_to_id_file, read_mapping_file


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

    def __set_iao(self):
        mapping_dict = read_mapping_file()
        tokenized_section_heading = nltk.wordpunct_tokenize(self.section_heading)
        text = nltk.Text(tokenized_section_heading)
        words = [w.lower() for w in text]
        h2_tmp = " ".join(word for word in words)

        # TODO: check for best match, not the first
        if h2_tmp != "":
            if any(x in h2_tmp for x in [" and ", "&", "/"]):
                mapping_result = []
                h2_parts = re.split(r" and |\s?/\s?|\s?&\s?", h2_tmp)
                for h2_part in h2_parts:
                    h2_part = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_part)
                    pass
                    for IAO_term, heading_list in mapping_dict.items():
                        if any(
                            [
                                fuzz.ratio(h2_part, heading) >= 80
                                for heading in heading_list
                            ]
                        ):
                            mapping_result.append(self.__add_iao(IAO_term))
                            break

            else:
                for IAO_term, heading_list in mapping_dict.items():
                    h2_tmp = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_tmp)
                    if any(
                        [fuzz.ratio(h2_tmp, heading) > 80 for heading in heading_list]
                    ):
                        mapping_result = [self.__add_iao(IAO_term)]
                        break
                    else:
                        mapping_result = []
        else:
            mapping_result = []
        if mapping_result == []:
            self.section_type = [{"iao_name": "document part", "iao_id": "IAO:0000314"}]
        else:
            self.section_type = mapping_result

    def __add_iao(self, iao_term):
        paper = {}
        iao_term = iao_term
        paper.update({self.section_heading: iao_term})

        # map IAO terms to IAO IDs
        iao_term_to_no_dict = read_iao_term_to_id_file()
        if iao_term in iao_term_to_no_dict.keys():
            mapping_result_id_version = iao_term_to_no_dict[iao_term]
        else:
            mapping_result_id_version = ""
        return {"iao_name": iao_term, "iao_id": mapping_result_id_version}

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
            self.paragraphs.append(
                References(ref, self.config, self.section_heading).to_dict()
            )

    def __init__(self, config, section_dict):
        """Identifies a section using the provided configuration.

        Args:
            config (Object): AC configuration object.
            section_dict (dict): Article section dictionary.
        """
        self.config = config
        self.section_heading = (
            section_dict["headers"][0]
            if "headers" in section_dict and not section_dict["headers"] == ""
            else ""
        )
        self.__set_iao()
        self.subheader = ""
        self.paragraphs = []
        if self.section_heading == "Abbreviations":
            self.__get_abbreviations(section_dict["node"])
        elif {
            "iao_name": "references section",
            "iao_id": "IAO:0000320",
        } in self.section_type:
            self.__get_references(section_dict["node"])
        else:
            self.__get_section(section_dict["node"])

    def to_list(self):
        """Retrieve a list of section paragraphs.

        Returns:
             (list): section paragraphs

        """
        return self.paragraphs if self.paragraphs else []
