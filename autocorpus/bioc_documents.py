"""
Script for handling construction of BioC documents.
"""
from pathlib import Path

from .bioc_passages import BioCPassage


class BiocDocument:
    """
    BioC Document builder
    """
    def build_passages(self, data_store):
        """
        Constructs the BioC document passages using the provided data store
        Args:
            data_store ([dict]):

        Returns:
            (list): list of BioC passages
        """
        seen_headings = []
        passages = [BioCPassage.from_title(data_store.main_text["title"], 0).as_dict()]
        if data_store.main_text["title"] not in seen_headings:
            offset = len(data_store.main_text["title"])
            seen_headings.append(data_store.main_text["title"])
        for passage in data_store.main_text["paragraphs"]:
            passage_obj = BioCPassage(passage, offset)
            passages.append(passage_obj.as_dict())
            offset += len(passage["body"])
            if passage["subsection_heading"] not in seen_headings:
                offset += len(passage["subsection_heading"])
                seen_headings.append(passage["subsection_heading"])
            if passage["section_heading"] not in seen_headings:
                offset += len(passage["section_heading"])
                seen_headings.append(passage["section_heading"])
        return passages

    def build_template(self, data_store):
        """
        Constructs the BioC document template using the provided data store
        Args:
            data_store ([dict]):
        Returns:
            (dict): BioC document complete populated with passages.
        """
        return {
            "id": Path(data_store.file_path).name.split(".")[0],
            "inputfile": data_store.file_path,
            "infons": {},
            "passages": self.build_passages(data_store),
            "annotations": [],
            "relations": [],
        }

    def __init__(self, input):
        self.document = self.build_template(input)
        pass

    def as_dict(self):
        """
        Return the BioC document as a dictionary
        Returns:
            (dict): BioC document as a dictionary
        """
        return self.document
