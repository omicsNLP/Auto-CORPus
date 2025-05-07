"""Handles section processing for Auto-CORPus.

Modules used:
- re: regular expression searching/replacing.
- nltk: string tokenization
- fuzzywuzzy: string-in-string ratio
"""

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib import resources
from itertools import chain
from typing import Any

import nltk
from bs4 import BeautifulSoup, Tag
from fuzzywuzzy import fuzz

from . import logger
from .reference import get_references
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


@dataclass
class Paragraph:
    """A paragraph for a section of the article."""

    section_heading: str
    subsection_heading: str
    body: str
    section_type: list[dict[str, str]]

    as_dict = asdict


def _get_abbreviations(
    abbreviations_config: dict[str, Any], soup_section: BeautifulSoup
) -> str:
    try:
        abbreviations_tables = handle_not_tables(abbreviations_config, soup_section)
        node = abbreviations_tables[0]["node"]
        abbreviations = {}
        for tr in node.find_all("tr"):
            short_form, long_form = (td.get_text() for td in tr.find_all("td"))
            abbreviations[short_form] = long_form
    except Exception:
        abbreviations = {}

    return str(abbreviations)


def _get_references(
    config: dict[str, Any], section_heading: str, soup_section: BeautifulSoup
) -> Iterable[dict[str, Any]]:
    """Constructs the article references using the provided configuration file.

    Args:
        config: HTML config rules
        section_heading: Current section heading
        soup_section: Article section containing references
    """
    all_references = handle_not_tables(config["references"], soup_section)
    for ref in all_references:
        yield get_references(ref, section_heading)


@dataclass(frozen=True)
class SectionChild:
    """A child node in the section."""

    subheading: str
    body: str


def _navigate_children(
    subheading: str,
    soup_sections: list[Tag],
    subsections: list[dict[str, Any]],
    paragraphs: list[Tag],
) -> Iterable[SectionChild]:
    for soup_section in soup_sections:
        if soup_section in paragraphs:
            if soup_section.previous_sibling and soup_section.previous_sibling.name in (  # type: ignore[attr-defined]
                "h3",
                "h4",
                "h5",
            ):
                subheading = soup_section.previous_sibling.get_text()
            yield SectionChild(subheading, soup_section.get_text())
            continue

        for subsec in subsections:
            if subsec["node"] == soup_section:
                subheading = (
                    subsec["headers"][0]
                    if "headers" in subsec and not subsec["headers"] == ""
                    else ""
                )

        try:
            children = soup_section.findChildren(recursive=False)
        except Exception as e:
            logger.warning(e)
            continue

        for output in _navigate_children(subheading, children, subsections, paragraphs):
            # We keep the last known subheading in case the next child doesn't define
            # their own
            subheading = output.subheading
            yield output


def _get_section(
    config: dict[str, Any], soup_section: BeautifulSoup
) -> Iterable[SectionChild]:
    subsections = handle_not_tables(config["sub-sections"], soup_section)
    paragraphs = [
        para["node"] for para in handle_not_tables(config["paragraphs"], soup_section)
    ]
    tables = [
        table["node"] for table in handle_not_tables(config["tables"], soup_section)
    ]
    figures = [
        figure["node"] for figure in handle_not_tables(config["figures"], soup_section)
    ]
    unwanted_paragraphs = list(
        chain.from_iterable(
            capt.find_all("p", recursive=True) for capt in chain(tables, figures)
        )
    )
    paragraphs = [para for para in paragraphs if para not in unwanted_paragraphs]
    children = soup_section.findChildren(recursive=False)
    return _navigate_children("", children, subsections, paragraphs)


def get_section(
    config: dict[str, dict[str, Any]], section_dict: dict[str, Any]
) -> Iterable[dict[str, Any]]:
    """Identifies a section using the provided configuration.

    Args:
        config: AC configuration object.
        section_dict: Article section dictionary.
    """
    section_heading = section_dict.get("headers", [""])[0]
    section_type = get_iao_term_mapping(section_heading)

    # Different processing for abbreviations and references section types
    if section_heading == "Abbreviations":
        if abbreviations_config := config.get("abbreviations-table", None):
            abbreviations = _get_abbreviations(
                abbreviations_config, section_dict["node"]
            )
            for body in abbreviations:
                yield Paragraph(section_heading, "", body, section_type).as_dict()
            return

    if {
        "iao_name": "references section",
        "iao_id": "IAO:0000320",
    } in section_type:
        yield from _get_references(config, section_heading, section_dict["node"])
        return

    for child in _get_section(config, section_dict["node"]):
        yield Paragraph(
            section_heading,
            child.subheading,
            child.body,
            section_type,
        ).as_dict()
