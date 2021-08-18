import re

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

	# def __get_paragraphs(self, soup_section):
	# 	body_select_tag = 'p,span'
	# 	header = self.__get_subsection_header(soup_section)
	# 	return {
	# 		"header": header,
	# 		"body": " ".join([i.get_text() for i in soup_section.select(body_select_tag)])
	# 	}

	def __add_paragraph(self, soup_section):
		self.paragraphs.append({
			"section_heading": self.section_heading,
			"subsection_heading": self.subheader,
			"body": soup_section.get_text()
		})

	def __navigate_children(self, soup_section, all_sub_sections, filtered_paragraphs):
		if soup_section in filtered_paragraphs:
			self.__add_paragraph(soup_section)
			return
		elif soup_section in all_sub_sections:
			self.subheader = self.__get_subsection_header(soup_section)
		try:
			children = soup_section.findChildren(recursive=False)
		except Exception as e:
			print(e)
			children=[]
		for child in children:
			self.__navigate_children(child, all_sub_sections, filtered_paragraphs)

	def __init__(self, config, soup_section):
		# TODO: separate out subsections and paragraphs from each section
		self.config = config
		self.section_heading = self.__get_section_header(soup_section)
		self.subheader = ""
		self.paragraphs = []
		all_subSections = soup_section.find_all(config['subsections']['name'], config['subsections']['attrs'])
		all_paragraphs = soup_section.find_all(config['paragraphs']['name'])
		filtered_paragraphs = []
		if config['paragraphs']['regex'] is not None:
			for para in all_paragraphs:
				for rePattern in config['paragraphs']['regex']:
					if para.has_attr(rePattern['attrs']):
						if re.match(rePattern['regex'], para.get(rePattern['attrs'])):
							filtered_paragraphs.append(para)
		children = soup_section.findChildren(recursive=False)
		for child in children:
			self.__navigate_children(child, all_subSections, filtered_paragraphs)

		# TODO: add logic for if there are no sections within the text, also change logic to look at section children
		#  one by one instead of look for sub sections to ensure correct order is retained if a section has a
		#  paragraph then a subsection
		pass

	def to_dict(self):
		return self.paragraphs
