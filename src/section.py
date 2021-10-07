import json
import re
from src.utils import *
from src.references import references

import nltk


class section:

	# def __get_section_header(self, soup_section):
	#
	# 	# if "sectionsNew" in config:
	# 	h2 = ""
	# 	h2_select_tag = self.config['heading']['name']
	# 	h2_select_tag += ''.join(['[{}*={}]'.format(k, self.config['heading']['attrs'][k])
	# 	                          for k in self.config['heading']['attrs'] if self.config['heading']['attrs'][k]])
	# 	_h2 = soup_section.select(h2_select_tag)
	# 	if _h2:
	# 		h2 = _h2[0].get_text().strip('\n')
	# 	return h2

	# def __get_subsection_header(self, soup_section):
	# 	h3_select_tag = self.config['heading2']['name']
	# 	h3_select_tag += ''.join(['[{}*={}]'.format(k, self.config['heading2']['attrs'][k])
	#                           for k in self.config['heading2']['attrs'] if self.config['heading2']['attrs'][k]])
	# 	h3 = soup_section.select(h3_select_tag)
	# 	if h3:
	# 		h3 = h3[0].get_text().strip('\n')
	# 	else:
	# 		h3 = ''
	# 	return h3

	def __add_paragraph(self, body):
		self.paragraphs.append({
			"section_heading": self.section_heading,
			"subsection_heading": self.subheader,
			"body": body,
			"section_type": self.section_type
		})

	def __navigate_children(self, soup_section, all_sub_sections, filtered_paragraphs):
		if soup_section in filtered_paragraphs:
			if soup_section.previous_sibling and soup_section.previous_sibling.name in ("h3", "h4", "h5"):
				self.subheader = soup_section.previous_sibling.get_text()
			self.__add_paragraph(soup_section.get_text())
			return
		for subsec in all_sub_sections:
			if subsec['node'] == soup_section:
				self.subheader = subsec['headers'][0] if "headers" in subsec and not subsec['headers'] == "" else ""
		# elif soup_section in subsecNodes:
		# 	self.subheader = self.__get_subsection_header(soup_section)
		try:
			children = soup_section.findChildren(recursive=False)
		except Exception as e:
			print(e)
			children=[]
		for child in children:
			self.__navigate_children(child, all_sub_sections, filtered_paragraphs)

	def __get_abbreviations(self, soup_section):
		if "abbreviations-table" in self.config:
			try:
				abbreviations_tables = handle_not_tables(self.config['abbreviations-table'], soup_section)
				abbreviations_tables = abbreviations_tables[0]['node']
				abbreviations = {}
				for tr in abbreviations_tables.find_all('tr'):
					short_form, long_form = [td.get_text() for td in tr.find_all('td')]
					abbreviations[short_form] = long_form
			except:
				abbreviations = {}
			self.__add_paragraph(str(abbreviations))

	def __set_IAO(self):
		mapping_dict = read_mapping_file()
		tokenized_section_heading = nltk.wordpunct_tokenize(self.section_heading)
		text = nltk.Text(tokenized_section_heading)
		## this .isalpha() should probably be removed as it;s stripping out &
		#words = [w.lower() for w in text if w.isalpha()]
		words = [w.lower() for w in text]
		h2_tmp = ' '.join(word for word in words)

	# TODO: check for best match, not the first
		if h2_tmp != '':
			if any(x in h2_tmp for x in [" and ", "&", "/"]):
				mapping_result = []
				h2_parts = re.split(" and |\s?/\s?|\s?&\s?", h2_tmp)
				for h2_part in h2_parts:
					h2_part = re.sub("^\d*\s?[\(\.]]?\s?", "", h2_part)
					pass
					for IAO_term, heading_list in mapping_dict.items():
						if any([fuzz.ratio(h2_part, heading) >= 80 for heading in heading_list]):
							mapping_result.append(self.__add_IAO(IAO_term))
							break

			else:
				for IAO_term, heading_list in mapping_dict.items():
					h2_tmp = re.sub("^\d*\s?[\(\.]]?\s?", "", h2_tmp)
					if any([fuzz.ratio(h2_tmp, heading) > 80 for heading in heading_list]):
						mapping_result = [self.__add_IAO(IAO_term)]
						break
					else:
						mapping_result = []
		else:
			h2 = ''
			mapping_result = []
		self.section_type = mapping_result

	def __add_IAO(self, IAO_term):
		paper = {}
		IAO_term = IAO_term
		paper.update({self.section_heading:IAO_term})
		# mapping_dict_with_DAG = assgin_heading_by_DAG(paper)
		#
		# if self.section_heading in mapping_dict_with_DAG.keys():
		# 	IAO_term = mapping_dict_with_DAG[self.section_heading]

		# map IAO terms to IAO IDs
		IAO_term_to_no_dict = read_IAO_term_to_ID_file()
		if IAO_term in IAO_term_to_no_dict.keys():
			mapping_result_ID_version = IAO_term_to_no_dict[IAO_term]
		else:
			mapping_result_ID_version = ''
		return {
			"iao_name": IAO_term,
			"iao_id": mapping_result_ID_version
		}

	def __get_section(self, soup_section):

		all_subSections = handle_not_tables(self.config['sub-sections'], soup_section)
		all_paragraphs = handle_not_tables(self.config['paragraphs'], soup_section)
		all_paragraphs = [x['node'] for x in all_paragraphs]
		all_tables = handle_not_tables(self.config['tables'], soup_section)
		all_tables = [x['node'] for x in all_tables]
		all_figures = handle_not_tables(self.config['figures'], soup_section)
		all_figures = [x['node'] for x in all_figures]
		# all_subSections = soup_section.find_all(self.config['subsections']['name'], self.config['subsections']['attrs'])
		# all_paragraphs = soup_section.find_all(self.config['paragraphs']['name'])
		# all_tables = soup_section.find_all(self.config['table-container']['name'], self.config['table-container']['attrs'])
		unwanted_paragraphs = []
		[unwanted_paragraphs.extend(capt.find_all("p", recursive=True)) for capt in all_tables]
		# all_figures = soup_section.find_all(self.config["figure"]["name"], self.config['figure']['attrs'])
		[unwanted_paragraphs.extend(capt.find_all("p", recursive=True)) for capt in all_figures]
		filtered_paragraphs = []
		all_paragraphs = [para for para in all_paragraphs if para not in unwanted_paragraphs]
		# if self.config['paragraphs']['regex'] is not None:
		# 	for para in all_paragraphs:
		# 		success=True
		# 		for rePattern in self.config['paragraphs']['regex']:
		# 			if para.has_attr(rePattern['attrs']):
		# 				if not re.match(rePattern['regex'], para.get(rePattern['attrs'])):
		# 					success=False
		# 			else:
		# 				success=False
		# 		if success:
		# 			filtered_paragraphs.append(para)
		children = soup_section.findChildren(recursive=False)
		for child in children:
			self.__navigate_children(child, all_subSections, all_paragraphs)

	def __get_references(self, soup_section):
		'''
		do somet with references here
		:return:
		'''
		all_references = handle_not_tables(self.config['references'], soup_section)
		for ref in all_references:
			self.paragraphs.append(references(ref, self.config, self.section_heading).to_dict())

	def __init__(self, config, sectionDict):

		self.config = config
		self.section_heading = sectionDict['headers'][0] if "headers" in sectionDict and not sectionDict['headers'] == "" else ""
		self.__set_IAO()
		self.subheader = ""
		self.paragraphs = []
		if self.section_heading == "Abbreviations":
			self.__get_abbreviations(sectionDict['node'])
		elif {"iao_name":"references section", "iao_id":"IAO:0000320"} in self.section_type:
			self.__get_references(sectionDict['node'])
		else:
			self.__get_section(sectionDict['node'])

	def to_dict(self):
		return self.paragraphs if self.paragraphs else []
