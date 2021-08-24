import os
import re
import nltk
import networkx as nx
from fuzzywuzzy import fuzz


def get_files(base_dir, pattern=r'(.*).html'):
    """
    recursively retrieve all PMC.html files from the directory

    Args: 
        base_dir: base directory

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
        if sup.string == None:
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
        if em.string == None:
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

def assgin_heading_by_DAG(paper):
    G = nx.read_graphml('src/DAG_model.graphml')
    mapping_dict_with_DAG = {}
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
    return mapping_dict_with_DAG
