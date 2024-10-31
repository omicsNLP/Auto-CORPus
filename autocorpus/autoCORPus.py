import argparse
import json
import sys
from pathlib import Path

from bioc import biocjson, biocxml
from bs4 import BeautifulSoup

from .abbreviation import abbreviations
from .bioc_formatter import BiocFormatter
from .section import section
from .table import table
from .table_image import table_image
from .utils import handle_not_tables


def handle_path(func):
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError as io:
            print(io)
            sys.exit()
        except OSError as exc:
            print(exc)
            sys.exit()
        except Exception as e:
            print(e)
            sys.exit()
        pass

    return inner_function


class autoCORPus:
    """ """

    @handle_path
    def __read_config(self, config_path):
        config_path = Path(config_path)
        with config_path.open("r") as f:
            ## TODO: validate config file here if possible
            content = json.load(f)
            return content["config"]

    @handle_path
    def __import_file(self, file_path):
        file_path = Path(file_path)
        with file_path.open("r") as f:
            return f.read(), file_path

    @handle_path
    def __handle_target_dir(self, target_dir):
        target_dir = Path(target_dir)
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
        return

    def __validate_infile(self):
        pass

    def __soupify_infile(self, fpath):
        fpath = Path(fpath)
        try:
            with open(fpath, encoding="utf-8") as fp:
                soup = BeautifulSoup(fp.read(), "html.parser")
                for e in soup.find_all(
                    attrs={"style": ["display:none", "visibility:hidden"]}
                ):
                    e.extract()
                return soup
        except Exception as e:
            print(e)

    def __clean_text(self, result):
        """
        clean the main text body output of extract_text() further as follows:
            remove duplicated texts from each section (assuming the text from html file has hierarchy up to h3, i.e. no subsubsections);
            remove items with empty bodies

        Args:
            result: dict of the maintext


        Return:
            result: cleaned dict of the maintext
        """
        # Remove duplicated contents from the 'result' output of extract_text()

        # Identify unique section headings and the index of their first appearance
        idx_section = []
        section_headings = set([i["section_heading"] for i in result["paragraphs"]])

        for i in range(len(section_headings)):
            try:
                if idx_section[i + 1] - idx_section[i] <= 1:  # if only one subsection
                    continue
                idx_section_last = idx_section[i + 1]
            except IndexError:
                idx_section_last = len(result["paragraphs"])

            p = result["paragraphs"][idx_section[i] + 1]["body"]
            for idx_subsection in range(idx_section[i] + 1, idx_section_last):
                if (
                    result["paragraphs"][idx_subsection]["body"]
                    in result["paragraphs"][idx_section[i]]["body"]
                ):
                    result["paragraphs"][idx_section[i]]["body"] = result["paragraphs"][
                        idx_section[i]
                    ]["body"].replace(result["paragraphs"][idx_subsection]["body"], "")

                if (idx_section[i] + 1 != idx_subsection) and (
                    p in result["paragraphs"][idx_subsection]["body"]
                ):
                    result["paragraphs"][idx_subsection]["body"] = result["paragraphs"][
                        idx_subsection
                    ]["body"].replace(p, "")
            for idx_subsection in range(idx_section[i] + 1, idx_section_last):
                if (
                    result["paragraphs"][idx_subsection]["subsection_heading"]
                    == result["paragraphs"][idx_section[i]]["subsection_heading"]
                ):
                    result["paragraphs"][idx_section[i]]["subsection_heading"] = ""
        return result

    def __get_keywords(self, soup, config):
        if "keywords" in config:
            responses = handle_not_tables(config["keywords"], soup)
            responses = " ".join([x["node"].get_text() for x in responses])
            if not responses == "":
                keywordSection = {
                    "section_heading": "keywords",
                    "subsection_heading": "",
                    "body": responses,
                    "section_type": [
                        {"iao_name": "keywords section", "iao_id": "IAO:0000630"}
                    ],
                }
                return [keywordSection]
            return False

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
        """
        convert beautiful soup object into a python dict object with cleaned main text body

        Args:
            soup: BeautifulSoup object of html

        Return:
            result: dict of the maintext
        """
        result = {}

        # Tags of text body to be extracted are hard-coded as p (main text) and span (keywords and refs)

        # Extract title
        # try:
        # 	h1 = soup.find(config['title']['name'],
        # 	               config['title']['attrs']).get_text().strip('\n')
        # except:
        # 	h1 = ''
        result["title"] = self.__get_title(soup, config)
        maintext = (
            self.__get_keywords(soup, config)
            if self.__get_keywords(soup, config)
            else []
        )
        sections = self.__get_sections(soup, config)
        # sections = [x['node'] for x in sections]
        for sec in sections:
            maintext.extend(section(config, sec).to_dict())
        # filter out the sections which do not contain any info
        filteredText = []
        [filteredText.append(x) for x in maintext if x]
        uniqueText = []
        seen_text = []
        for text in filteredText:
            if text["body"] not in seen_text:
                seen_text.append(text["body"])
                uniqueText.append(text)

        result["paragraphs"] = self.__set_unknown_section_headings(uniqueText)

        return result

    def __set_unknown_section_headings(self, uniqueText):
        paper = {}
        for para in uniqueText:
            if para["section_heading"] != "keywords":
                paper[para["section_heading"]] = [
                    x["iao_name"] for x in para["section_type"]
                ]

        for text in uniqueText:
            if not text["section_heading"]:
                text["section_heading"] = "document part"
                text["section_type"] = [
                    {"iao_name": "document part", "iao_id": "IAO:0000314"}
                ]

        # uniqueText = [x for x in uniqueText if x['section_heading']]
        # mapping_dict_with_DAG = assgin_heading_by_DAG(paper)
        # for i, para in enumerate(uniqueText):
        #     if para['section_heading'] in mapping_dict_with_DAG.keys():
        #         if para['section_type'] == []:
        #             uniqueText[i]['section_type'] = mapping_dict_with_DAG[para['section_heading']]
        return uniqueText

    def __handle_html(self, file_path, config):
        """
        handles common HTML processing elements across main_text and linked_tables (creates soup and parses tables)
        :return: soup object
        """

        soup = self.__soupify_infile(file_path)
        if "tables" in config:
            if self.tables == {}:
                self.tables, self.empty_tables = table(
                    soup, config, file_path, self.base_dir
                ).to_dict()
            else:
                seenIDs = set()
                for tab in self.tables["documents"]:
                    if "." in tab["id"]:
                        seenIDs.add(tab["id"].split(".")[0])
                    else:
                        seenIDs.add(tab["id"])
                tmp_tables, tmp_empty = table(
                    soup, config, file_path, self.base_dir
                ).to_dict()
                for tabl in tmp_tables["documents"]:
                    if "." in tabl["id"]:
                        tabl_id = tabl["id"].split(".")[0]
                        tabl_pos = ".".join(tabl["id"].split(".")[1:])
                    else:
                        tabl_id = tabl["id"]
                        tabl_pos = None
                    if tabl_id in seenIDs:
                        tabl_id = str(len(seenIDs) + 1)
                        if tabl_pos:
                            tabl["id"] = f"{tabl_id}.{tabl_pos}"
                        else:
                            tabl["id"] = tabl_id
                    seenIDs.add(tabl_id)
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
                seenIDs = {}
                for i, table in enumerate(self.tables["documents"]):
                    if "id" in table:
                        seenIDs[str(i)] = f"Table {table['id']}."
                for table in self.empty_tables:
                    for seenID in seenIDs.keys():
                        if table["title"].startswith(seenIDs[seenID]):
                            if "title" in table and not table["title"] == "":
                                setNew = False
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
                                        setNew = True
                                if not setNew:
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
                                setNew = False
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
                                        setNew = True
                                if not setNew:
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
                                setNew = False
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
                                        setNew = True
                                if not setNew:
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

    def __init__(
        self,
        config_path,
        base_dir=None,
        main_text=None,
        linked_tables=None,
        table_images=None,
        associated_data_path=None,
        trainedData=None,
    ):
        """

        :param config_path: path to the config file to be used
        :param file_path: path to the main text of the article (HTML files only)
        :param linked_tables: list of linked table file paths to be included in this run (HTML files only)
        :param table_images: list of table image file paths to be included in this run (JPEG or PNG files only)
        :param associated_data_path: this still needs sorting
        """
        # handle common
        config = self.__read_config(config_path)
        self.base_dir = base_dir
        self.file_path = main_text
        self.main_text = {}
        self.empty_tables = {}
        self.tables = {}
        self.abbreviations = {}
        self.has_tables = False

        # handle main_text
        if self.file_path:
            soup = self.__handle_html(self.file_path, config)
            self.main_text = self.__extract_text(soup, config)
            try:
                self.abbreviations = abbreviations(
                    self.main_text, soup, config, self.file_path
                ).to_dict()
            except Exception as e:
                print(e)
        if linked_tables:
            for table_file in linked_tables:
                soup = self.__handle_html(table_file, config)
        if table_images:
            self.tables = table_image(
                table_images, self.base_dir, trainedData=trainedData
            ).to_dict()
        self.__merge_table_data()
        if "documents" in self.tables and not self.tables["documents"] == []:
            self.has_tables = True

    def to_bioc(self):
        return BiocFormatter(self).to_dict()

    def main_text_to_bioc_json(self, indent=2):
        return BiocFormatter(self).to_json(indent)

    def main_text_to_bioc_xml(self):
        collection = biocjson.loads(BiocFormatter(self).to_json(2))
        return biocxml.dumps(collection)

    def tables_to_bioc_json(self, indent=2):
        return json.dumps(self.tables, ensure_ascii=False, indent=indent)

    def abbreviations_to_bioc_json(self, indent=2):
        return json.dumps(self.abbreviations, ensure_ascii=False, indent=indent)

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_dict(self):
        return {
            "main_text": self.main_text,
            "abbreviations": self.abbreviations,
            "tables": self.tables,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--filepath", type=str, help="filepath of html file to be processed"
    )
    parser.add_argument(
        "-t", "--target_dir", type=str, help="target directory for output"
    )
    parser.add_argument(
        "-c", "--config", type=str, help="filepath for configuration JSON file"
    )
    parser.add_argument(
        "-d", "--config_dir", type=str, help="directory of configuration JSON files"
    )
    parser.add_argument(
        "-a", "--associated_data", type=str, help="directory of associated data"
    )
    args = parser.parse_args()
    filepath = args.filepath
    target_dir = args.target_dir
    config_path = args.config

    autoCORPus(config_path, filepath, target_dir).to_file(target_dir)
