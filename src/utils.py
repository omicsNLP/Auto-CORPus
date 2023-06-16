import os
import re
import unicodedata

import bs4
import networkx as nx
from bs4 import NavigableString
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
            IAO_term = line.split('\t')[1].lower().strip('\n')
            if IAO_term != '':
                if '/' in IAO_term:
                    IAO_term_1 = IAO_term.split('/')[0].strip(' ')
                    IAO_term_2 = IAO_term.split('/')[1].strip(' ')
                    if IAO_term_1 in mapping_dict.keys():
                        mapping_dict[IAO_term_1].append(heading)
                    else:
                        mapping_dict.update({IAO_term_1: [heading]})

                    if IAO_term_2 in mapping_dict.keys():
                        mapping_dict[IAO_term_2].append(heading)
                    else:
                        mapping_dict.update({IAO_term_2: [heading]})

                else:
                    if IAO_term in mapping_dict.keys():
                        mapping_dict[IAO_term].append(heading)
                    else:
                        mapping_dict.update({IAO_term: [heading]})
    return mapping_dict


def read_IAO_term_to_ID_file():
    IAO_term_to_no_dict = {}
    with open('src/IAO_dicts/IAO_term_to_ID.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            IAO_term = line.split('\t')[0]
            IAO_no = line.split('\t')[1].strip('\n')
            IAO_term_to_no_dict.update({IAO_term: IAO_no})
    return IAO_term_to_no_dict


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
    bsAttrs = {
        "name": [],
        "attrs": [],
        "xpath": []
    }
    if "tag" in definition:
        bsAttrs['name'] = config_tags(definition['tag'])
    if "attrs" in definition:
        bsAttrs['attrs'] = config_attrs(definition['attrs'])
    if "xpath" in definition:
        bsAttrs['xpath'] = definition['xpath']
    return bsAttrs


def clean_tag_content(tag, soup):
    """
    Remove leading and trailing whitespace & newline characters from soup tags recursively.
    tag: BeautifulSoup tag or NavigableString
    soup: The parent beautifulsoup object.
    """
    if isinstance(tag, NavigableString):
        return tag.strip()
    else:
        new_tag = soup.new_tag(tag.name)
        for child in tag.children:
            cleaned_child = clean_tag_content(child, soup)
            new_tag.append(cleaned_child)
        return new_tag


def handle_defined_by(config, soup):
    '''

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
	'''
    if "defined-by" not in config:
        quit(F"{config} does not contain the required 'defined-by' key.")
    matches = []
    seen_text = []
    for definition in config['defined-by']:
        bsAttrs = parse_configs(definition)
        new_matches = []
        if bsAttrs["name"] or bsAttrs["attrs"]:
            new_matches = soup.find_all(bsAttrs['name'], bsAttrs['attrs'])
            if new_matches:
                new_matches = [x for x in new_matches if x.text]
        if "xpath" in bsAttrs:
            if type(bsAttrs["xpath"]) == list:
                for path in bsAttrs["xpath"]:
                    xpath_matches = fromstring(str(soup)).xpath(path)
                    if xpath_matches:
                        for new_match in xpath_matches:
                            new_match = bs4.BeautifulSoup(etree.tostring(new_match, encoding="unicode", method="html"),
                                                          "html.parser")
                            if new_match.text.strip():
                                new_matches.extend(new_match)
            else:
                xpath_matches = fromstring(str(soup)).xpath(bsAttrs["xpath"])
                if xpath_matches:
                    for new_match in xpath_matches:
                        new_match = bs4.BeautifulSoup(etree.tostring(new_match, encoding="unicode", method="html"),
                                                      "html.parser")
                        if new_match.text.strip():
                            new_matches.extend(new_match)
        for match in new_matches:
            if type(match) != NavigableString:
                matched_text = match.get_text()
            if matched_text in seen_text:
                continue
            else:
                seen_text.append(matched_text)
                matches.append(match)

    # clean up the match texts
    matches = [clean_tag_content(match, soup) for match in matches]

    return matches


def handle_not_tables(config, soup):
    responses = []
    matches = handle_defined_by(config, soup)
    if "data" in config:
        for match in matches:
            responseAddition = {
                "node": match
            }
            for ele in config['data']:
                seen_text = set()
                for definition in config['data'][ele]:
                    bsAttrs = parse_configs(definition)
                    newMatches = match.find_all(bsAttrs['name'], bsAttrs['attrs'])
                    if newMatches:
                        responseAddition[ele] = []
                    for newMatch in newMatches:
                        if newMatch.get_text() in seen_text:
                            continue
                        else:
                            responseAddition[ele].append(newMatch.get_text())
            responses.append(responseAddition)
    else:
        for match in matches:
            responseAddition = {
                "node": match
            }
            responses.append(responseAddition)
    return responses


def get_data_element_node(config, soup):
    config = {
        "defined-by": config
    }
    return handle_defined_by(config, soup)


def navigate_contents(item):
    value = ""
    xa = u'\xa0'
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
    textData = [
        "caption",
        "title",
        "footer"
    ]
    if "data" in config:
        for match in matches:
            responseAddition = {
                "node": match,
                "title": "",
                "footer": "",
                "caption": ""
            }
            for ele in config['data']:
                if ele in textData:
                    seen_text = set()
                    for definition in config['data'][ele]:
                        bsAttrs = parse_configs(definition)
                        newMatches = match.find_all(bsAttrs['name'], bsAttrs['attrs'])
                        if newMatches:
                            responseAddition[ele] = []
                        for newMatch in newMatches:
                            if newMatch.get_text() in seen_text:
                                continue
                            else:
                                value = ""
                                for item in newMatch.contents:
                                    value += navigate_contents(item)
                                    # clean the cell
                                value = value.strip().replace('\u2009', ' ')
                                value = re.sub("<\/?span[^>\n]*>?|<hr\/>?", "", value)
                                value = re.sub("\\n", "", value)
                                responseAddition[ele].append(value)
            responses.append(responseAddition)
    else:
        for match in matches:
            responseAddition = {
                "node": match
            }
            responses.append(responseAddition)
    return responses


def assgin_heading_by_DAG(paper):
    G = nx.read_graphml('src/DAG_model.graphml')
    new_mapping_dict = {}
    mapping_dict_with_DAG = {}
    IAO_term_to_no_dict = read_IAO_term_to_ID_file()
    for i, heading in enumerate(paper.keys()):
        if paper[heading] == []:
            previous_mapped_heading_found = False
            i2 = 1
            while not previous_mapped_heading_found:
                if i - i2 > len(list(paper.keys())):
                    previous_mapped_heading_found = True
                    previous_section = "Start of the article"
                else:
                    previous_heading = list(paper.keys())[i - i2]
                    if paper[previous_heading] != []:
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
                    if paper[next_heading] != []:
                        next_mapped_heading_found = True
                        next_section = paper[next_heading]
                    else:
                        i2 += 1

            if previous_section != "Start of the article" and next_section != "End of the article":
                try:
                    paths = nx.all_shortest_paths(
                        G, paper[previous_heading][-1], paper[next_heading][0], weight='cost')
                    for path in paths:
                        if len(path) <= 2:
                            mapping_dict_with_DAG.update({heading: [path[0]]})
                        if len(path) > 2:
                            mapping_dict_with_DAG.update({heading: path[1:-1]})
                except:
                    new_target = paper[list(paper.keys())[i + i2 + 1]][0]
                    paths = nx.all_shortest_paths(
                        G, paper[previous_heading][-1], new_target, weight='cost')
                    for path in paths:
                        if len(path) == 2:
                            mapping_dict_with_DAG.update({heading: [path[0]]})
                        if len(path) > 2:
                            mapping_dict_with_DAG.update({heading: path[1:-1]})

            if next_section == "End of the article":
                mapping_dict_with_DAG.update({heading: [previous_section[-1]]})

            for heading in mapping_dict_with_DAG.keys():
                newSecType = []
                for secType in mapping_dict_with_DAG[heading]:
                    if secType in IAO_term_to_no_dict.keys():
                        mapping_result_ID_version = IAO_term_to_no_dict[secType]
                    else:
                        mapping_result_ID_version = ''
                    newSecType.append({
                        "iao_name": secType,
                        "iao_id": mapping_result_ID_version
                    })

                new_mapping_dict[heading] = newSecType
    return new_mapping_dict
