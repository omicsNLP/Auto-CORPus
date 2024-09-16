from pathlib import Path

from src.bioc_passages import BioCPassage


class BiocDocument:

    def build_passages(self, data_store):
        seen_headings = []
        data_store.main_text['title'] = data_store.main_text['title'].strip()
        passages = [BioCPassage.from_title(data_store.main_text['title'], 0).as_dict()]
        offset = 0
        if data_store.main_text['title'] not in seen_headings:
            offset = len(data_store.main_text['title'])
            seen_headings.append(data_store.main_text['title'])
        for passage in data_store.main_text['paragraphs']:
            passage["body"] = passage["body"].strip()
            passage["section_heading"] = passage["section_heading"].strip()
            passage["subsection_heading"] = passage["subsection_heading"].strip()
            passage_obj = BioCPassage(passage, offset)
            passages.append(passage_obj.as_dict())
            offset += len(passage['body'])
            if passage['subsection_heading'] not in seen_headings:
                offset += len(passage['subsection_heading'])
                seen_headings.append(passage['subsection_heading'])
            if passage['section_heading'] not in seen_headings:
                offset += len(passage['section_heading'])
                seen_headings.append(passage['section_heading'])
        return passages

    def build_template(self, data_store):
        return {
            "id": Path(data_store.file_path).name.split(".")[0],
            "inputfile": data_store.file_path,
            "infons": {},
            "passages": self.build_passages(data_store),
            "annotations": [],
            "relations": []
        }

    def __init__(self, document_data):
        self.document = self.build_template(document_data)
        pass

    def as_dict(self):
        return self.document
