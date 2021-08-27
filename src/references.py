import re

class references():

	def __get_section_header(self, soup_section):
		h2 = ""
		h2_select_tag = self.config['heading']['name']
		h2_select_tag += ''.join(['[{}*={}]'.format(k, self.config['heading']['attrs'][k])
		                          for k in self.config['heading']['attrs'] if self.config['heading']['attrs'][k]])
		_h2 = soup_section.select(h2_select_tag)
		if _h2:
			h2 = _h2[0].get_text().strip('\n')
		return h2
		pass

	def __get_subsection_header(self, soup_section):
		h3_select_tag = self.config['heading2']['name']
		h3_select_tag += ''.join(['[{}*={}]'.format(k, self.config['heading2']['attrs'][k])
		                          for k in self.config['heading2']['attrs'] if self.config['heading2']['attrs'][k]])
		h3 = soup_section.select(h3_select_tag)
		if h3:
			h3 = h3[0].get_text().strip('\n')
		else:
			h3 = ''
		return h3
		pass

	def __create_reference_block(self, reference):
		refSection = {
			"section_heading": self.section_heading,
			"subsection_heading": "",
			"body": reference.get_text().replace("Go to:", ""),
			"section_type": [
				{
					"IAO_term": "references section",
					"IAO_id": "IAO:0000320"
				}
			]
		}

		for subsec in self.config['references']['sections']:
			sect = reference.find(self.config['references']['sections'][subsec]['name'], self.config['references']['sections'][subsec]['attrs'])
			if sect:
				refSection[subsec] = sect.get_text()

		return refSection

	def __init__(self, soup, config, section_heading):
		self.config = config
		self.section_heading = section_heading


		self.reference = self.__create_reference_block(soup)

	def to_dict(self):
		return self.reference
