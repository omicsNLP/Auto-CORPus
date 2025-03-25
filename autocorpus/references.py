"""Use regular expression for searching/replacing reference strings."""

import re


class References:
    """Class for processing references using an input soup object and references config."""

    def __create_reference_block(self, reference):
        text = reference["node"].get_text().replace("Go to:", "").replace("\n", "")
        text = re.sub(r"\s{2,}", " ", text)
        ref_section = {
            "section_heading": self.section_heading,
            "subsection_heading": "",
            "body": text,
            "section_type": [
                {"iao_name": "references section", "iao_id": "IAO:0000320"}
            ],
        }

        for sub_sec in reference:
            if sub_sec == "node":
                continue
            ref_section[sub_sec] = ". ".join(reference[sub_sec])

        return ref_section

    def __init__(self, soup, config, section_heading):
        """References constructor using provided AC config rules and input soup article data.

        Args:
            soup (BeautifulSoup): BeautifulSoup object
            config (Object): AutoCorpus configuration references object
            section_heading (str): Section heading string
        """
        self.config = config
        self.section_heading = section_heading

        self.reference = self.__create_reference_block(soup)

    def to_dict(self):
        """Return the reference BioC dictionary block.

        Returns:
             (dict): Reference BioC dictionary.
        """
        return self.reference
