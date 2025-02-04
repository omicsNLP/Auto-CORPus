"""Use regular expression for searching/replacing reference strings.
"""
import re


class References:
    """Class for processing references using an input soup object and references config.
    """
    #
    # def __get_section_header(self, soup_section):
    # 	h2 = ""
    # 	h2_select_tag = self.config['heading']['name']
    # 	h2_select_tag += ''.join(['[{}*={}]'.format(k, self.config['heading']['attrs'][k])
    # 	                          for k in self.config['heading']['attrs'] if self.config['heading']['attrs'][k]])
    # 	_h2 = soup_section.select(h2_select_tag)
    # 	if _h2:
    # 		h2 = _h2[0].get_text().strip('\n')
    # 	return h2
    # 	pass
    #
    # def __get_subsection_header(self, soup_section):
    # 	h3_select_tag = self.config['heading2']['name']
    # 	h3_select_tag += ''.join(['[{}*={}]'.format(k, self.config['heading2']['attrs'][k])
    # 	                          for k in self.config['heading2']['attrs'] if self.config['heading2']['attrs'][k]])
    # 	h3 = soup_section.select(h3_select_tag)
    # 	if h3:
    # 		h3 = h3[0].get_text().strip('\n')
    # 	else:
    # 		h3 = ''
    # 	return h3
    # 	pass

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
        """Args:
        soup (BeautifulSoup): BeautifulSoup object
        config (Object): AutoCorpus configuration references object
        section_heading (str): Section heading string
        """
        self.config = config
        self.section_heading = section_heading

        self.reference = self.__create_reference_block(soup)

    def to_dict(self):
        """Return the reference BioC dictionary block.
        Returns (dict): Reference BioC dictionary.

        """
        return self.reference
