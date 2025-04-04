"""Utility script containing various functions used throughout AC in different use-cases."""

import re
import unicodedata
from pathlib import Path

import bs4
from bs4 import NavigableString
from lxml import etree
from lxml.html.soupparser import fromstring


def get_files(base_dir, pattern=r"(.*).html"):
    """Recursively retrieve all PMC.html files from the directory.

    Args:
        base_dir: base directory
        pattern: file name filter REGEX pattern (default *.html)

    Return:
        file_list: a list of filepath

    """
    file_list = []
    base_dir = Path(base_dir)
    for item in base_dir.iterdir():
        abs_path = item.resolve()
        if abs_path.is_file() and re.match(pattern, str(abs_path)):
            file_list.append(str(abs_path))
        elif abs_path.is_dir() and "ipynb_checkpoints" not in str(abs_path):
            file_list += get_files(abs_path, pattern)
    return file_list


def config_anchors(value):
    """Clean the regex anchors of an AC config rule.

    Args:
        value (str): AC config anchor value

    Returns:
        (str): Cleaned regex with missing ^ and $ characters added.
    """
    if not value.startswith("^"):
        value = f"^{value}"
    if not value.endswith("$"):
        value = f"{value}$"
    return value


def config_attr_block(block):
    """Parse the attributes block of an AC config file.

    Args:
        block (dict): attributes block of an AC config file

    Returns:
        (dict) regex compiled & cleaned attributes block
    """
    ret = {}
    for key in block:
        if isinstance(block[key], list):
            ret[key] = [re.compile(config_anchors(x)) for x in block[key]]
        elif isinstance(block[key], str):
            ret[key] = re.compile(config_anchors(block[key]))
    return ret


def config_attrs(attrs):
    """Clean and compile attributes block of an AC config file.

    Args:
        attrs (list of dicts or dict): attributes block of an AC config file

    Returns:
        (list): cleaned and compiled attributes block of an AC config file
    """
    ret = []
    if isinstance(attrs, list):
        for attr in attrs:
            ret.extend(config_attr_block(attr))
    elif isinstance(attrs, dict):
        ret = config_attr_block(attrs)
    else:
        quit(f"{attrs} must be a dict or a list of dicts")
    return ret


def config_tags(tags):
    """Parse the tags block of an AC config file.

    Args:
        tags (list or str): tags block of an AC config file

    Returns:
        (list): cleaned and compiled tags block of an AC config file
    """
    ret = []
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str):
                ret.append(re.compile(config_anchors(tag)))
            else:
                quit(f"{tags} must be a string or list of strings")
    elif isinstance(tags, str):
        ret.append(re.compile(config_anchors(tags)))
    else:
        quit(f"{tags} must be a string or list of strings")
    return ret


def parse_configs(definition):
    """Parse a top-level block of an AC config file.

    Args:
        definition (dict): top-level block of an AC config file.

    Returns:
        (dict): cleaned and compiled block of an AC config file.
    """
    bs_attrs = {"name": [], "attrs": [], "xpath": []}
    if "tag" in definition:
        bs_attrs["name"] = config_tags(definition["tag"])
    if "attrs" in definition:
        bs_attrs["attrs"] = config_attrs(definition["attrs"])
    if "xpath" in definition:
        bs_attrs["xpath"] = definition["xpath"]
    return bs_attrs


def handle_defined_by(config, soup):
    """Retrieve matching nodes for the 'defined-by' config rules.

    Args:
        config (dict): config file section used to parse
        soup (bs4.BeautifulSoup): soup section to parse

    Returns:
        (list): list of objects, each object being a matching node. Object of the form:
                {
                        node: bs4Object,
                        data:{
                                        key: [values]
                                }
                }
        node is a bs4 object of a single result derived from bs4.find_all()
        data is an object where the results from the config "data" sections is housed. The key is the name of the data
        section and the values are all matches found within any of the main matches which match the current data section
        definition. The values is the response you get from get_text() on any found nodes, not the nodes themselves.
    """
    if "defined-by" not in config:
        quit(f"{config} does not contain the required 'defined-by' key.")
    matches = []
    seen_text = []
    for definition in config["defined-by"]:
        bs_attrs = parse_configs(definition)
        new_matches = []
        if bs_attrs["name"] or bs_attrs["attrs"]:
            new_matches = soup.find_all(
                bs_attrs["name"] if bs_attrs["name"] else None,
                bs_attrs["attrs"] if bs_attrs["attrs"] else None,
            )
            if new_matches:
                new_matches = [x for x in new_matches if x.text]
        if "xpath" in bs_attrs:
            if isinstance(bs_attrs["xpath"], list):
                for path in bs_attrs["xpath"]:
                    xpath_matches = fromstring(str(soup)).xpath(path)
                    if xpath_matches:
                        for new_match in xpath_matches:
                            new_match = bs4.BeautifulSoup(
                                etree.tostring(
                                    new_match, encoding="unicode", method="html"
                                ),
                                "html.parser",
                            )
                            if new_match.text.strip():
                                new_matches.extend(new_match)
            else:
                xpath_matches = fromstring(str(soup)).xpath(bs_attrs["xpath"])
                if xpath_matches:
                    for new_match in xpath_matches:
                        new_match = bs4.BeautifulSoup(
                            etree.tostring(
                                new_match, encoding="unicode", method="html"
                            ),
                            "html.parser",
                        )
                        if new_match.text.strip():
                            new_matches.extend(new_match)
        for match in new_matches:
            if type(match) is not NavigableString:
                matched_text = match.get_text()
            if matched_text in seen_text:
                continue
            else:
                seen_text.append(matched_text)
                matches.append(match)
    return matches


def handle_not_tables(config, soup):
    """Executes a search on non-table bs4 soup objects based on provided config rules.

    Args:
        config (dict): Parsed config rules to be used
        soup (bs4.BeautifulSoup): BeautifulSoup object containing the input text to search

    Returns:
        (list): Matches for the provided config rules
    """
    responses = []
    matches = handle_defined_by(config, soup)
    if "data" in config:
        for match in matches:
            response_addition = {"node": match}
            for ele in config["data"]:
                seen_text = set()
                for definition in config["data"][ele]:
                    bs_attrs = parse_configs(definition)
                    new_matches = match.find_all(
                        bs_attrs["name"] if bs_attrs["name"] else None,
                        bs_attrs["attrs"] if bs_attrs["attrs"] else None,
                    )
                    if new_matches:
                        response_addition[ele] = []
                    for newMatch in new_matches:
                        if newMatch.get_text() in seen_text:
                            continue
                        else:
                            response_addition[ele].append(newMatch.get_text())
            responses.append(response_addition)
    else:
        for match in matches:
            response_addition = {"node": match}
            responses.append(response_addition)
    return responses


def get_data_element_node(config, soup):
    """Retrieve the matches for the data element node config rules.

    Args:
        config (dict): Parsed config rules to be used
        soup (bs4.BeautifulSoup): BeautifulSoup object containing the input text to search

    Returns:
        (list): Matches for the data element node config rules
    """
    config = {"defined-by": config}
    return handle_defined_by(config, soup)


def navigate_contents(item):
    """Extract nested text recursively from the provided NavigableString/Tag item.

    Args:
        item (bs4.element.NavigableString or bs4.element.Tag): Root element/tag to extract nested text from.

    Returns:
        (str) Text nested within the provided item.
    """
    value = ""
    if isinstance(item, bs4.element.NavigableString):
        value += unicodedata.normalize("NFKD", item)
    if isinstance(item, bs4.element.Tag):
        if item.name == "sup" or item.name == "sub":
            value += "<" + item.name + ">"
            for childItem in item.contents:
                value += navigate_contents(childItem)
            value += "</" + item.name + ">"
        else:
            for childItem in item.contents:
                value += navigate_contents(childItem)
    return value


def handle_tables(config, soup):
    """Parse the provided BeautifulSoup object containing tables using the provided config rules.

    Args:
        config (dict): Parsed config rules to be used
        soup (bs4.BeautifulSoup): BeautifulSoup object containing the input tables to construct

    Returns:
        (list): List of matches for the provided config rules
    """
    responses = []
    matches = handle_defined_by(config, soup)
    text_data = ["caption", "title", "footer"]
    if "data" in config:
        for match in matches:
            response_addition = {
                "node": match,
                "title": "",
                "footer": "",
                "caption": "",
            }
            for ele in config["data"]:
                if ele in text_data:
                    seen_text = set()
                    for definition in config["data"][ele]:
                        bs_attrs = parse_configs(definition)
                        new_matches = match.find_all(
                            bs_attrs["name"] if bs_attrs["name"] else None,
                            bs_attrs["attrs"] if bs_attrs["attrs"] else None,
                        )
                        if new_matches:
                            response_addition[ele] = []
                        for newMatch in new_matches:
                            if newMatch.get_text() in seen_text:
                                continue
                            else:
                                value = ""
                                for item in newMatch.contents:
                                    value += navigate_contents(item)

                                # clean the cell
                                value = value.strip().replace("\u2009", " ")
                                value = re.sub("<\\/?span[^>\n]*>?|<hr\\/>?", "", value)
                                value = re.sub("\\n", "", value)
                                response_addition[ele].append(value)
            responses.append(response_addition)
    else:
        for match in matches:
            response_addition = {"node": match}
            responses.append(response_addition)
    return responses
