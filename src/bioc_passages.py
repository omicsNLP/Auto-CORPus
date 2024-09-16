class BioCPassage:

    @classmethod
    def from_title(cls, title, offset):
        title_passage = {
            "section_heading": "",
            "subsection_heading": "",
            "body": title,
            "section_type": [
                {
                    "iao_name": "document title",
                    "iao_id": "IAO:0000305"
                }
            ]

        }
        return cls(title_passage, offset)

    @staticmethod
    def __build_passage(passage, offset):
        defaultkeys = ["section_heading", "subsection_heading", "body", "section_type"]
        passage_dict = {
            "offset": offset,
            "infons": {},
            "text": passage['body'],
            "sentences": [],
            "annotations": [],
            "relations": []
        }
        for key in passage.keys():
            if key not in defaultkeys:
                passage_dict['infons'][key] = passage[key]
        # TODO: currently assumes section_heading and subsection_heading will always exist, should ideally check for
        #  existence. Also doesn't account for sub-subsection headings which might exist
        if passage['section_heading'] != "":
            passage_dict['infons']['section_title_1'] = passage['section_heading']
        if passage['subsection_heading'] != "":
            passage_dict['infons']['section_title_2'] = passage["subsection_heading"]
        counter = 1
        for section_type in passage["section_type"]:
            passage_dict['infons'][F"iao_name_{counter}"] = section_type['iao_name']
            passage_dict['infons'][F"iao_id_{counter}"] = section_type['iao_id']
            counter += 1

        return passage_dict

    def __init__(self, passage, offset):
        self.offset = 0
        self.passage = self.__build_passage(passage, offset)
        pass

    def as_dict(self):
        return self.passage
