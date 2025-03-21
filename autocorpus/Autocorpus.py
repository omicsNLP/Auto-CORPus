"""Auto-CORPus primary functions are called from this script, after initialisation with __main__.py."""

import argparse
import json
from pathlib import Path

from bioc import biocjson, biocxml
from bs4 import BeautifulSoup

from .abbreviation import Abbreviations
from .bioc_formatter import BiocFormatter
from .section import Section
from .table import Table
from .tableimage import TableImage
from .utils import handle_not_tables


class Autocorpus:
    """Parent class for all Auto-CORPus functionality."""

    def __read_config(self, config_path):
        config_path = Path(config_path)
        with config_path.open("r") as f:
            ## TODO: validate config file here if possible
            content = json.load(f)
            return content["config"]

    def __import_file(self, file_path):
        file_path = Path(file_path)
        with file_path.open("r") as f:
            return f.read(), file_path

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

    def __clean_text(self, result: dict) -> dict:
        r"""Clean the main text body output of extract_text().

        - removes duplicated texts from each section (assuming the text from html file has hierarchy up to h3, i.e. no subsubsections)
        - removes items with empty bodies.

        Args:
            result (dict): dict of the maintext


        Return:
            (dict): cleaned dict result input

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
                keyword_section = {
                    "section_heading": "keywords",
                    "subsection_heading": "",
                    "body": responses,
                    "section_type": [
                        {"iao_name": "keywords section", "iao_id": "IAO:0000630"}
                    ],
                }
                return [keyword_section]
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
        """Convert beautiful soup object into a python dict object with cleaned main text body.

        Args:
            soup (bs4.BeautifulSoup): BeautifulSoup object of html
            config (dict): AC config rules

        Return:
            (dict): dict of the maintext
        """
        result = {}

        # Tags of text body to be extracted are hard-coded as p (main text) and span (keywords and refs)
        result["title"] = self.__get_title(soup, config)
        maintext = (
            self.__get_keywords(soup, config)
            if self.__get_keywords(soup, config)
            else []
        )
        sections = self.__get_sections(soup, config)
        for sec in sections:
            maintext.extend(Section(config, sec).to_list())

        # filter out the sections which do not contain any info
        filtered_text = []
        [filtered_text.append(x) for x in maintext if x]
        unique_text = []
        seen_text = []
        for text in filtered_text:
            if text["body"] not in seen_text:
                seen_text.append(text["body"])
                unique_text.append(text)

        result["paragraphs"] = self.__set_unknown_section_headings(unique_text)

        return result

    def __set_unknown_section_headings(self, unique_text):
        paper = {}
        for para in unique_text:
            if para["section_heading"] != "keywords":
                paper[para["section_heading"]] = [
                    x["iao_name"] for x in para["section_type"]
                ]

        for text in unique_text:
            if not text["section_heading"]:
                text["section_heading"] = "document part"
                text["section_type"] = [
                    {"iao_name": "document part", "iao_id": "IAO:0000314"}
                ]

        return unique_text

    def __handle_html(self, file_path, config):
        """Handles common HTML processing elements across main_text and linked_tables (creates soup and parses tables).

        Args:
            file_path (str): path to the main text file
            config (dict): dict of the maintext
        Return:
            (bs4.BeautifulSoup): soup object
        """
        soup = self.__soupify_infile(file_path)
        if "tables" in config:
            if self.tables == {}:
                self.tables, self.empty_tables = Table(
                    soup, config, file_path, self.base_dir
                ).to_dict()
            else:
                seen_ids = set()
                for tab in self.tables["documents"]:
                    if "." in tab["id"]:
                        seen_ids.add(tab["id"].split(".")[0])
                    else:
                        seen_ids.add(tab["id"])
                tmp_tables, tmp_empty = Table(
                    soup, config, file_path, self.base_dir
                ).to_dict()
                for tabl in tmp_tables["documents"]:
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
                seen_ids = {}
                for i, table in enumerate(self.tables["documents"]):
                    if "id" in table:
                        seen_ids[str(i)] = f"Table {table['id']}."
                for table in self.empty_tables:
                    for seenID in seen_ids.keys():
                        if table["title"].startswith(seen_ids[seenID]):
                            if "title" in table and not table["title"] == "":
                                set_new = False
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
                                        set_new = True
                                if not set_new:
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
                                set_new = False
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
                                        set_new = True
                                if not set_new:
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
                                set_new = False
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
                                        set_new = True
                                if not set_new:
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
        trained_data=None,
    ):
        """Utilises the input config file to create valid BioC versions of input HTML journal articles.

        Args:
            config_path (str): path to the config file to be used
            base_dir (str): base directory of the input HTML journal articles
            main_text (str): path to the main text of the article (HTML files only)
            linked_tables (list): list of linked table file paths to be included in this run (HTML files only)
            table_images (list): list of table image file paths to be included in this run (JPEG or PNG files only)
            associated_data_path (str): currently unused
            trained_data (str): currently unused, previously added for image processing
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
                self.abbreviations = Abbreviations(
                    self.main_text, soup, config, self.file_path
                ).to_dict()
            except Exception as e:
                print(e)
        if linked_tables:
            for table_file in linked_tables:
                soup = self.__handle_html(table_file, config)
        if table_images:
            self.tables = TableImage(
                table_images, self.base_dir, trained_data=trained_data
            ).to_dict()
        self.__merge_table_data()
        if "documents" in self.tables and not self.tables["documents"] == []:
            self.has_tables = True

    def to_bioc(self):
        """Get the currently loaded bioc as a dict.

        Returns:
            (dict): bioc as a dict
        """
        return BiocFormatter(self).to_dict()

    def main_text_to_bioc_json(self, indent=2):
        """Get the currently loaded main text as BioC JSON.

        Args:
            indent (int): level of indentation

        Returns:
            (str): main text as BioC JSON
        """
        return BiocFormatter(self).to_json(indent)

    def main_text_to_bioc_xml(self):
        """Get the currently loaded main text as BioC XML.

        Returns:
            (str): main text as BioC XML
        """
        collection = biocjson.loads(BiocFormatter(self).to_json(2))
        return biocxml.dumps(collection)

    def tables_to_bioc_json(self, indent=2):
        """Get the currently loaded tables as Tables-JSON.

        Args:
            indent (int): level of indentation

        Returns:
            (str): tables as Tables-JSON
        """
        return json.dumps(self.tables, ensure_ascii=False, indent=indent)

    def abbreviations_to_bioc_json(self, indent=2):
        """Get the currently loaded abbreviations as BioC JSON.

        Args:
            indent (int): level of indentation

        Returns:
            (str): abbreviations as BioC JSON
        """
        return json.dumps(self.abbreviations, ensure_ascii=False, indent=indent)

    def to_json(self, indent=2):
        """Get the currently loaded AC object as a dict.

        Args:
            indent (int): Level of indentation.

        Returns:
            (str): AC object as a JSON string
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_dict(self):
        """Get the currently loaded AC object as a dict.

        Returns:
            (dict): AC object as a dict
        """
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

    Autocorpus(config_path, filepath, target_dir).to_file(target_dir)
