import json
import re
from src.utils import *
from src.references import references

import nltk


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

	def __add_paragraph(self, body):
		self.paragraphs.append({
			"section_heading": self.section_heading,
			"subsection_heading": self.subheader,
			"body": body,
			"section_type": self.section_type
		})

	def __navigate_children(self, soup_section, all_sub_sections, filtered_paragraphs):
		if soup_section in filtered_paragraphs:
			self.__add_paragraph(soup_section.get_text())
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

	def __get_abbreviations(self, soup_section):
		try:
			abbreviations_table = soup_section.find(self.config['abbreviations_table']['name'], self.config['abbreviations_table']['attrs'])
			abbreviations = {}
			for tr in abbreviations_table.find_all('tr'):
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

		if h2_tmp != '':
			if any(x in h2_tmp for x in [" and ", "&", "/"]):
				mapping_result = []
				h2_parts = re.split(" and |\s?/\s?|\s?&\s?", h2_tmp)
				for h2_part in h2_parts:
					for IAO_term, heading_list in mapping_dict.items():
						if any([fuzz.ratio(h2_part, heading) >= 94 for heading in heading_list]):
							mapping_result.append(self.__add_IAO(IAO_term))
							break

			else:
				for IAO_term, heading_list in mapping_dict.items():
					if any([fuzz.ratio(h2_tmp, heading) > 95 for heading in heading_list]):
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
		mapping_dict_with_DAG = assgin_heading_by_DAG(paper)

		if self.section_heading in mapping_dict_with_DAG.keys():
			IAO_term = mapping_dict_with_DAG[self.section_heading]

		# map IAO terms to IAO IDs
		IAO_term_to_no_dict = read_IAO_term_to_ID_file()
		if IAO_term in IAO_term_to_no_dict.keys():
			mapping_result_ID_version = IAO_term_to_no_dict[IAO_term]
		else:
			mapping_result_ID_version = ''
		return {
			"IAO_term": IAO_term,
			"IAO_id": mapping_result_ID_version
		}

	def __get_section(self, soup_section):
		all_subSections = soup_section.find_all(self.config['subsections']['name'], self.config['subsections']['attrs'])
		all_paragraphs = soup_section.find_all(self.config['paragraphs']['name'])
		all_tables = soup_section.find_all(self.config['table-tom']['name'], self.config['table-tom']['attrs'])
		unwanted_paragraphs = []
		[unwanted_paragraphs.extend(capt.find_all("p", recursive=True)) for capt in all_tables]
		all_figures = soup_section.find_all(self.config["figure"]["name"], self.config['figure']['attrs'])
		[unwanted_paragraphs.extend(capt.find_all("p", recursive=True)) for capt in all_figures]
		filtered_paragraphs = []
		all_paragraphs = [para for para in all_paragraphs if para not in unwanted_paragraphs]
		if self.config['paragraphs']['regex'] is not None:
			for para in all_paragraphs:
				success=True
				for rePattern in self.config['paragraphs']['regex']:
					if para.has_attr(rePattern['attrs']):
						if not re.match(rePattern['regex'], para.get(rePattern['attrs'])):
							success=False
					else:
						success=False
				if success:
					filtered_paragraphs.append(para)
		children = soup_section.findChildren(recursive=False)
		for child in children:
			self.__navigate_children(child, all_subSections, filtered_paragraphs)

	def __get_references(self, soup_section):
		'''
		do somet with references here
		:return:
		'''
		all_references = []
		for defined in self.config["references"]["defined"]:
			all_references.extend(soup_section.find_all(defined["name"], defined["attrs"]))
		if "regex" in self.config['references'].keys():
			for reStyle in self.config['references']["regex"]:
				kwargs = {reStyle['attrs'] : re.compile(reStyle['regex'])}
				all_references.extend(soup_section.find_all(reStyle["name"], **kwargs, recursive=True))
		for ref in all_references:
			self.paragraphs.append(references(ref, self.config, self.section_heading).to_dict())

	def __init__(self, config, soup_section, file_name):
		self.file_name = file_name
		self.config = config
		self.section_heading = self.__get_section_header(soup_section)
		self.__set_IAO()
		self.subheader = ""
		self.paragraphs = []
		if self.section_heading == "Abbreviations":
			self.__get_abbreviations(soup_section)
		elif {"IAO_term":"references section", "IAO_id":"IAO:0000320"} in self.section_type:
			self.__get_references(soup_section)
			pass
		else:
			self.__get_section(soup_section)



		# TODO: add logic for if there are no sections within the text, also change logic to look at section children
		#  one by one instead of look for sub sections to ensure correct order is retained if a section has a
		#  paragraph then a subsection
		pass

	def to_dict(self):
		return self.paragraphs
