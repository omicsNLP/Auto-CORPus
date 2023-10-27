import os
import re
import unicodedata

import bs4
import networkx as nx
from bs4 import NavigableString, Tag
from lxml import etree
from lxml.html.soupparser import fromstring


def get_files(base_dir, pattern=r'(.*).html'):
    """
    recursively retrieve all PMC.html files from the directory

    Args:
        base_dir: base directory
        pattern: file name filter REGEX pattern (default *.html)

    Return:
        file_list: a list of filepath
    """
    file_list = []
    files = os.listdir(base_dir)
    for i in files:
        abs_path = os.path.join(base_dir, i)
        if re.match(pattern, abs_path):
            file_list.append(abs_path)
        elif os.path.isdir(abs_path) & ('ipynb_checkpoints' not in abs_path):
            file_list += get_files(abs_path)
    return file_list


def process_supsub(soup):
    """
    add underscore (_) before all superscript or subscript text

    Args:
        soup: BeautifulSoup object of html

    """
    # for sup in soup.find_all(['sup', 'sub']):
    for sup in soup.find_all('sub'):
        s = sup.get_text()
        if sup.string is None:
            sup.extract()
        elif re.match('[_-]', s):
            sup.string.replace_with('{} '.format(s))
        else:
            sup.string.replace_with('_{} '.format(s))
    return soup


def process_em(soup):
    """
    remove all emphasized text
    No it doesn't, it just adds a space to it

    Args:
        soup: BeautifulSoup object of html

    """
    for em in soup.find_all('em'):
        s = em.get_text()
        if em.string is None:
            em.extract()
        else:
            em.string.replace_with('{} '.format(s))
    return soup


def read_mapping_file():
    mapping_dict = {}
    with open('src/IAO_dicts/IAO_FINAL_MAPPING.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            heading = line.split('\t')[0].lower().strip('\n')
            iao_term = line.split('\t')[1].lower().strip('\n')
            if iao_term != '':
                if '/' in iao_term:
                    iao_term_1 = iao_term.split('/')[0].strip(' ')
                    iao_term_2 = iao_term.split('/')[1].strip(' ')
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


def read_iao_term_to_id_file():
    iao_term_to_no_dict = {}
    with open('src/IAO_dicts/IAO_term_to_ID.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            iao_term = line.split('\t')[0]
            iao_no = line.split('\t')[1].strip('\n')
            iao_term_to_no_dict.update({iao_term: iao_no})
    return iao_term_to_no_dict


def config_anchors(value):
    if not value.startswith("^"):
        value = F"^{value}"
    if not value.endswith("$"):
        value = F"{value}$"
    return value


def config_attr_block(block):
    ret = {}
    for key in block:
        if isinstance(block[key], list):
            ret[key] = [re.compile(config_anchors(x)) for x in block[key]]
        elif isinstance(block[key], str):
            ret[key] = re.compile(config_anchors(block[key]))
    return ret


def config_attrs(attrs):
    ret = []
    if isinstance(attrs, list):
        for attr in attrs:
            ret.extend(config_attr_block(attr))
    elif isinstance(attrs, dict):
        ret = config_attr_block(attrs)
    else:
        quit(F"{attrs} must be a dict or a list of dicts")
    return ret


def config_tags(tags):
    ret = []
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str):
                ret.append(re.compile(config_anchors(tag)))
            else:
                quit(F"{tags} must be a string or list of strings")
    elif isinstance(tags, str):
        ret.append(re.compile(config_anchors(tags)))
    else:
        quit(F"{tags} must be a string or list of strings")
    return ret


def parse_configs(definition):
    bs_attrs = {
        "name": [],
        "attrs": [],
        "xpath": []
    }
    if "tag" in definition:
        bs_attrs['name'] = config_tags(definition['tag'])
    if "attrs" in definition:
        bs_attrs['attrs'] = config_attrs(definition['attrs'])
    if "xpath" in definition:
        bs_attrs['xpath'] = definition['xpath']
    return bs_attrs


def recursively_strip_strings(tag):
    """
    Remove leading and trailing whitespace & newline characters from soup tags recursively.
    tag: BeautifulSoup tag or NavigableString
    """
    for child in tag.contents:
        if isinstance(child, Tag):
            recursively_strip_strings(child)
        elif isinstance(child, str):
            child = child.strip()


def handle_defined_by(config, soup):
    """
	:param config: config file section used to parse
	:param soup: soup section to parse
	:return:
	list of objects, each object being a matching node. Object of the form:
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
        quit(F"{config} does not contain the required 'defined-by' key.")
    matches = []
    seen_text = []
    for definition in config['defined-by']:
        bs_attrs = parse_configs(definition)
        new_matches = []
        if bs_attrs["name"] or bs_attrs["attrs"]:
            new_matches = soup.find_all(bs_attrs['name'], bs_attrs['attrs'])
            if new_matches:
                new_matches = [x for x in new_matches if x.text]
        if "xpath" in bs_attrs:
            if type(bs_attrs["xpath"]) is list:
                for path in bs_attrs["xpath"]:
                    xpath_matches = fromstring(str(soup)).xpath(path)
                    if xpath_matches:
                        for new_match in xpath_matches:
                            new_match = bs4.BeautifulSoup(etree.tostring(new_match, encoding="unicode", method="html"),
                                                          "html.parser")
                            if new_match.text.strip():
                                new_matches.extend(new_match)
            else:
                xpath_matches = fromstring(str(soup)).xpath(bs_attrs["xpath"])
                if xpath_matches:
                    for new_match in xpath_matches:
                        new_match = bs4.BeautifulSoup(etree.tostring(new_match, encoding="unicode", method="html"),
                                                      "html.parser")
                        if new_match.text.strip():
                            new_matches.extend(new_match)
        for match in new_matches:
            matched_text = None
            if type(match) is not NavigableString:
                matched_text = match.get_text()
            if matched_text in seen_text:
                continue
            else:
                seen_text.append(matched_text)
                matches.append(match)

    # clean up the match texts
    # currently unused due to unexpected removal of outputs
    # for tag in matches:
    #     recursively_strip_strings(tag)
    return matches


def rearrange_segmented_elements(tag_list, seperator_tag):
    """
    Creates a new structure for problematic matches returned containing no complete section containers.
    New structure will group repeated tag patterns together into sections based on the input seperator_tag string.
    :param tag_list: list of matches (tag objects)
	:param seperator_tag: HTML tag name (string)
	:return: List of Tag objects (list)
    """
    parent_tags = []  # List to store the parent tags

    current_parent = None  # Variable to store the current parent tag

    for tag in tag_list:
        if tag.name == seperator_tag:
            # If the current tag is a seperator tag, create a new parent tag
            current_parent = Tag(name='div')
            current_parent.append(tag)
            parent_tags.append(current_parent)
        elif current_parent is not None:
            # If the current tag is not an <h2> tag and a parent tag exists
            current_parent.append(tag)

    return parent_tags


def handle_not_tables(config, soup):
    responses = []
    matches = handle_defined_by(config, soup)
    # check layout of publication structure
    # segmented layout is sibling elements throughout rather than containers for each section.
    is_segmented_layout = False
    type_count = len(set([x.name for x in matches]))
    if type_count > 1:
        is_segmented_layout = True
    if "data" in config:
        if is_segmented_layout:
            matches = rearrange_segmented_elements(matches, matches[0].name)
        for match in matches:
            response_addition = {
                "node": match
            }
            for ele in config['data']:
                seen_text = set()
                for definition in config['data'][ele]:
                    bs_attrs = parse_configs(definition)
                    new_matches = match.find_all(definition["tag"], bs_attrs['attrs'])
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
            response_addition = {
                "node": match
            }
            responses.append(response_addition)
    return responses


def get_data_element_node(config, soup):
    config = {
        "defined-by": config
    }
    return handle_defined_by(config, soup)


def navigate_contents(item):
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
    responses = []
    matches = handle_defined_by(config, soup)
    text_data = [
        "caption",
        "title",
        "footer"
    ]
    if "data" in config:
        for match in matches:
            response_addition = {
                "node": match,
                "title": "",
                "footer": "",
                "caption": ""
            }
            for ele in config['data']:
                if ele in text_data:
                    seen_text = set()
                    for definition in config['data'][ele]:
                        bs_attrs = parse_configs(definition)
                        new_matches = match.find_all(bs_attrs['name'], bs_attrs['attrs'])
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
                                value = value.strip().replace('\u2009', ' ')
                                value = re.sub(r"</?span[^>\n]*>?|<hr/>?", "", value)
                                value = re.sub(r"\\n", "", value)
                                response_addition[ele].append(value)
            responses.append(response_addition)
    else:
        for match in matches:
            response_addition = {
                "node": match
            }
            responses.append(response_addition)
    return responses


def assign_heading_by_dag(paper):
    g = nx.read_graphml('src/DAG_model.graphml')
    new_mapping_dict = {}
    mapping_dict_with_dag = {}
    iao_term_to_no_dict = read_iao_term_to_id_file()
    previous_section = ""
    next_section = ""
    previous_heading = ""
    next_heading = ""

    for i, heading in enumerate(paper.keys()):
        if not paper[heading]:
            previous_mapped_heading_found = False
            i2 = 1
            while not previous_mapped_heading_found:
                if i - i2 > len(list(paper.keys())):
                    previous_mapped_heading_found = True
                    previous_section = "Start of the article"
                else:
                    previous_heading = list(paper.keys())[i - i2]
                    if paper[previous_heading]:
                        previous_mapped_heading_found = True
                        previous_section = paper[previous_heading]
                    else:
                        i2 += 1

            next_mapped_heading_found = False
            i2 = 1
            while not next_mapped_heading_found:
                if i + i2 >= len(list(paper.keys())):
                    next_mapped_heading_found = True
                    next_section = "End of the article"
                else:
                    next_heading = list(paper.keys())[i + i2]
                    if paper[next_heading]:
                        next_mapped_heading_found = True
                        next_section = paper[next_heading]
                    else:
                        i2 += 1

            if previous_section != "Start of the article" and next_section != "End of the article":
                try:
                    paths = nx.all_shortest_paths(
                        g, paper[previous_heading][-1], paper[next_heading][0], weight='cost')
                    for path in paths:
                        if len(path) <= 2:
                            mapping_dict_with_dag.update({heading: [path[0]]})
                        if len(path) > 2:
                            mapping_dict_with_dag.update({heading: path[1:-1]})
                except:
                    new_target = paper[list(paper.keys())[i + i2 + 1]][0]
                    paths = nx.all_shortest_paths(
                        g, paper[previous_heading][-1], new_target, weight='cost')
                    for path in paths:
                        if len(path) == 2:
                            mapping_dict_with_dag.update({heading: [path[0]]})
                        if len(path) > 2:
                            mapping_dict_with_dag.update({heading: path[1:-1]})

            if next_section == "End of the article":
                mapping_dict_with_dag.update({heading: [previous_section[-1]]})

            for i_heading in mapping_dict_with_dag.keys():
                new_sec_type = []
                for secType in mapping_dict_with_dag[i_heading]:
                    if secType in iao_term_to_no_dict.keys():
                        mapping_result_id_version = iao_term_to_no_dict[secType]
                    else:
                        mapping_result_id_version = ''
                    new_sec_type.append({
                        "iao_name": secType,
                        "iao_id": mapping_result_id_version
                    })

                new_mapping_dict[i_heading] = new_sec_type
    return new_mapping_dict


def is_number(s):
    """
    check if input string is a number

    Args:
        s: input string

    Returns:
        True/False

    """
    try:
        float(s.replace(',', ''))
        return True
    except ValueError:
        return False


def is_mixed_data_type(s):
    """
    check if input string is a mix of number and text

    Args:
        s: input string

    Returns:
        True/False

    """
    if any(char.isdigit() for char in s):
        if any(char for char in s if char.isdigit() is False):
            return True
    return False


def is_text(s):
    """
    check if input string is all text

    Args:
        s: input string

    Returns:
        True/False

    """
    if any(char.isdigit() for char in s):
        return False
    return True


class BioCTable:
    """
    Converts tables from nested lists into a BioC table object.
    """

    def __init__(self, input_file, table_id, table_data):
        self.inputfile = input_file
        self.id = str(table_id) + "_1"
        self.infons = {}
        self.passages = []
        self.annotations = []
        self.__build_table(table_data)

    def __build_table(self, table_data):
        """
        Builds a table passage based on the provided table_data and adds it to the passages list.

        Args:
            table_data: A pandas DataFrame containing the data for the table.

        Returns:
            None
        """
        # Create a title passage
        title_passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_title",
                "iao_name_1": "document title",
                "iao_id_1": "IAO:0000305"
            },
        }
        self.passages.append(title_passage)
        # Create a caption passage
        caption_passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_caption",
                "iao_name_1": "caption",
                "iao_id_1": "IAO:0000304"
            },
        }
        self.passages.append(caption_passage)
        # Create a passage for table content
        passage = {
            "offset": 0,
            "infons": {
                "section_title_1": "table_content",
                "iao_name_1": "table",
                "iao_id_1": "IAO:0000306"
            },
            "column_headings": [],
            "data_section": [
                {
                    "table_section_title_1": "",
                    "data_rows": [

                    ]
                }
            ]
        }
        # Populate column headings
        for i, text in enumerate(table_data.columns.values):
            passage["column_headings"].append(
                {
                    "cell_id": self.id + F".1.{i + 1}",
                    "cell_text": replace_unicode(text)
                }
            )
        # Populate table rows with cell data
        for row_idx, row in enumerate(table_data.values):
            new_row = []
            for cell_idx, cell in enumerate(row):
                new_cell = {
                    "cell_id": F"{self.id}.{row_idx + 2}.{cell_idx + 1}",
                    "cell_text": F"{replace_unicode(cell)}"
                }
                new_row.append(new_cell)
            passage["data_section"][0]["data_rows"].append(new_row)
        # Add the table passage to the passages list
        self.passages.append(passage)


def replace_unicode(text):
    """
    Replaces specific Unicode characters in a given text.

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
                    t.replace('\u00a0', ' ').replace('\u00ad', '-').replace('\u2010', '-').replace('\u00d7', 'x'))
            else:
                clean_texts.append(t)
        return clean_texts
    else:
        if type(text) is str:
            clean_text = text.replace('\u00a0', ' ').replace('\u00ad', '-').replace('\u2010', '-').replace('\u00d7',
                                                                                                           'x')
        else:
            clean_text = text
        return clean_text
