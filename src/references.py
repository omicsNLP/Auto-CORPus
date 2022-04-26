import re


class References:

    def __create_reference_block(self, reference):
        text = reference['node'].get_text().replace("Go to:", "").replace("\n", "")
        text = re.sub(r"\s{2,}", " ", text)
        ref_section = {
            "section_heading": self.section_heading,
            "subsection_heading": "",
            "body": text,
            "section_type": [
                {
                    "iao_name": "references section",
                    "iao_id": "IAO:0000320"
                }
            ]
        }

        for subsec in reference:
            if subsec == "node":
                continue
            ref_section[subsec] = ". ".join(reference[subsec])

        return ref_section

    def __init__(self, soup, config, section_heading):
        self.config = config
        self.section_heading = section_heading

        self.reference = self.__create_reference_block(soup)

    def to_dict(self):
        return self.reference
