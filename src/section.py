class section:
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

	def __get_paragraphs(self, soup_section):
		body_select_tag = 'p,span'
		return [" ".join([i.get_text() for i in soup_section.select(body_select_tag)])]

	def __init__(self, config, soup_section):
		self.config = config
		self.section_heading = self.__get_section_header(soup_section)
		self.subsection_heading = self.__get_subsection_header(soup_section)
		self.paragraphs = self.__get_paragraphs(soup_section)
		pass

	def to_dict(self):
		return_list = []
		for paragraph in self.paragraphs:
			return_list.append({
				"section_heading": self.section_heading,
				"subsection_heading": self.subsection_heading,
				"body": paragraph
			})
		return return_list
