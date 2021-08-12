import json
import sys
from bs4 import BeautifulSoup
import os
import pytest
import errno
import re
import regex as re2
from src.utils import *
import argparse
from src.section import section
from collections import defaultdict, Counter
import logging
from src.abbreviation import abbreviations
from src.table import table
from src.table_image import table_image

def handle_path(func):
	def inner_function(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except IOError as io:
			print(io)
			sys.exit()
		except OSError as exc:
			print(exc)
			sys.exit()
		except Exception as e:
			print(e)
			sys.exit()
		pass
	return inner_function



class autoCORPus:
	'''
	TODO: read in file path
		TODO: error handling
	TODO: read in target directory
		TODO: create target directory if needed
		TODO error handling
	TODO: read in config
		TODO: validate config file
		TODO: error handling
	TODO: extract maintext
		TODO: extract individual paragraphs, not just sections
		TODO: extract individual references
		TODO: error handling
	TODO: extract abbreviations
		TODO: error handling
	TODO: extract tables
		TODO: error handling
	TODO: output in AC format
		TODO: error handling
	TODO: output in BioC format
		TODO: error handling

	redo of the HTML parsing:

	1) find the main body of text
	2) find each section within the main body
	3) discard sections we dont want
	4) for each section identify it's section type (abstract, intro etc) + title
	5) identify inner sections for each main section + their titles
	6) for each inner section identify paragraphs
	'''

	@classmethod
	def from_stream(cls):
		'''
		stream a response from requests directly into autocorpus
		import lxml.html
		import requests

		url =  "http://www.example.com/servlet/av/ResultTemplate=AVResult.html"
		response = requests.get(url, stream=True)
		response.raw.decode_content = True
		tree = lxml.html.parse(response.raw)
		:return:
		'''
		pass

	@handle_path
	def __read_config(self, config_path):
		with open(config_path, "r") as f:
			## TODO: validate config file here if possible
			return json.load(f)

	@handle_path
	def __import_file(self, file_path):
		with open(file_path, "r") as f:
			return f.read(), file_path

	@handle_path
	def __handle_target_dir(self, target_dir):
		for dir in ["maintext", "tables", "abbreviations"]:
			if not os.path.exists(f"{target_dir}/{dir}"):
				os.makedirs(f"{target_dir}/{dir}")
		return target_dir

	def __validate_infile(self):
		pass



	def __soupify_infile(self):
		try:
			soup = BeautifulSoup(self.text, 'html.parser')
			for e in soup.find_all(attrs={'style': ['display:none', 'visibility:hidden']}):
				e.extract()
			# what to do with in sentence reference
			for ref in soup.find_all(attrs={'class': ['supplementary-material', 'figpopup', 'popnode', 'bibr']}):
				ref.extract()
			soup = process_supsub(soup)
			soup = process_em(soup)
			return soup
		except Exception as e:
			print(e)

	def __clean_text(self, result):
		'''
		clean the main text body output of extract_text() further as follows:
			remove duplicated texts from each section (assuming the text from html file has hierarchy up to h3, i.e. no subsubsections);
			remove items with empty bodies

		Args:
			result: dict of the maintext


		Return:
			result: cleaned dict of the maintext
		'''
		# Remove duplicated contents from the 'result' output of extract_text()

		# Identify unique section headings and the index of their first appearance
		section_unique = []
		idx_section = []
		section_headings = [i['section_heading'] for i in result['paragraphs']]
		i = 0
		for heading in section_headings:
			if heading not in section_unique:
				section_unique.append(heading)
				idx_section.append(i)
			i += 1

		for i in range(len(section_unique)):
			try:
				if idx_section[i+1]-idx_section[i] <= 1:  # if only one subsection
					continue
				idx_section_last = idx_section[i+1]
			except IndexError:
				idx_section_last = len(result['paragraphs'])

			p = result['paragraphs'][idx_section[i]+1]['body']
			for idx_subsection in range(idx_section[i]+1, idx_section_last):
				if result['paragraphs'][idx_subsection]['body'] in result['paragraphs'][idx_section[i]]['body']:
					result['paragraphs'][idx_section[i]]['body'] = result['paragraphs'][idx_section[i]]['body'].replace(
						result['paragraphs'][idx_subsection]['body'], '')

				if (idx_section[i]+1 != idx_subsection) and (p in result['paragraphs'][idx_subsection]['body']):
					result['paragraphs'][idx_subsection]['body'] = result['paragraphs'][idx_subsection]['body'].replace(
						p, '')
			for idx_subsection in range(idx_section[i]+1, idx_section_last):
				if result['paragraphs'][idx_subsection]['subsection_heading'] == result['paragraphs'][idx_section[i]]['subsection_heading']:
					result['paragraphs'][idx_section[i]]['subsection_heading'] = ''

		result['paragraphs'] = [
			p for p in result['paragraphs'] if p['body'].replace('Go to:', '').strip() != '']
		return result


	def __extract_text(self, soup, config):
		"""
		convert beautiful soup object into a python dict object with cleaned main text body

		Args:
			soup: BeautifulSoup object of html

		Return:
			result: dict of the maintext
		"""
		result = {}

		# Tags of text body to be extracted are hard-coded as p (main text) and span (keywords and refs)
		body_select_tag = 'p,span'

		# Extract title
		try:
			h1 = soup.find(config['title']['name'],
			               config['title']['attrs']).get_text().strip('\n')
		except:
			h1 = ''
		result['title'] = h1

		maintext = []
		sections = soup.find_all(config['body']['name'], config['body']['attrs'])
		for p in sections:
			paragraph = {}
			h2_select_tag = config['heading']['name']
			h2_select_tag += ''.join(['[{}*={}]'.format(k, config['heading']['attrs'][k])
			                          for k in config['heading']['attrs'] if config['heading']['attrs'][k]])

			h3_select_tag = config['heading2']['name']
			h3_select_tag += ''.join(['[{}*={}]'.format(k, config['heading2']['attrs'][k])
			                          for k in config['heading2']['attrs'] if config['heading2']['attrs'][k]])

			_h2 = p.select(h2_select_tag)
			if _h2:
				h2 = _h2[0].get_text().strip('\n')

			h3 = p.select(h3_select_tag)

			if h3:
				h3 = h3[0].get_text().strip('\n')
			else:
				h3 = ''
			try:
				paragraph['section_heading'] = h2
			except UnboundLocalError:
				paragraph['section_heading'] = ''
			paragraph['subsection_heading'] = h3
			paragraph['body'] = ' '.join([i.get_text()
			                              for i in p.select(body_select_tag)])
			maintext.append(paragraph)

		result['paragraphs'] = maintext
		return self.__clean_text(result)

	def __add_IAO_ids(self):
		paper = {}
		paragraphs = self.main_text['paragraphs']
		for paragraph in paragraphs:
			h2 = paragraph['section_heading']
			IAO_term = paragraph['IAO_term']
			paper.update({h2:IAO_term})

		mapping_dict_with_DAG = assgin_heading_by_DAG(paper)
		for paragraph in paragraphs:
			h2 = paragraph['section_heading']
			if h2 in mapping_dict_with_DAG.keys():
				paragraph.update({'IAO_term':mapping_dict_with_DAG[h2]})

		# map IAO terms to IAO IDs
		IAO_term_to_no_dict = read_IAO_term_to_ID_file()
		for paragraph in paragraphs:
			mapping_result_ID_version = []
			IAO_terms = paragraph['IAO_term']
			if IAO_terms != '' and IAO_terms != []:
				for IAO_term in IAO_terms:
					if IAO_term in IAO_term_to_no_dict.keys():
						mapping_result_ID_version.append(IAO_term_to_no_dict[IAO_term])
			else:
				mapping_result_ID_version = ''
			paragraph.update({'IAO_ID':mapping_result_ID_version})
		self.main_text['paragraphs'] = paragraphs

	def __init__(self, config_path, file_path, associated_data_path=None):
		self.text, self.file_path = self.__import_file(file_path)
		self.config=self.__read_config(config_path)
		self.soup = self.__soupify_infile()
		self.main_text = read_maintext_json(self.__extract_text(self.soup, self.config))
		# TODO: incorporate the below line into the above
		self.__add_IAO_ids()
		self.abbreviations = abbreviations(self.main_text, self.soup, self.config).to_dict()
		self.tables = table(self.soup, self.config).to_dict()
		image_path = os.path.join(self.file_path, 'image')
		if os.path.isdir(image_path):
			self.table_images = table_image(self.config, image_path)
		pass

	def to_json(self):
		outlist =  [self.main_text, self.abbreviations, self.tables]
		return json.dumps(outlist, ensure_ascii=False, indent=2)

	@handle_path
	def to_file(self, target_dir):
		target_dir = self.__handle_target_dir(target_dir)
		file_name = self.file_path.split("/")[-1].replace(".html", "").strip()
		with open(f"{target_dir}/maintext/{file_name}_maintext.json", "w") as outfile:
			json.dump(self.main_text,outfile,ensure_ascii=False, indent=2)
		with open(f"{target_dir}/tables/{file_name}_tables.json", "w") as outfile:
			json.dump(self.tables,outfile,ensure_ascii=False, indent=2)
		with open(f"{target_dir}/abbreviations/{file_name}_abbreviations.json", "w") as outfile:
			json.dump(self.abbreviations,outfile,ensure_ascii=False, indent=2)


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--filepath", type=str,
	                    help="filepath of of html file to be processed")
	parser.add_argument("-t", "--target_dir", type=str,
	                    help="target directory for output")
	parser.add_argument("-c", "--config", type=str,
	                    help="filepath for configuration JSON file")
	parser.add_argument("-d", "--config_dir", type=str, help="directory of configuration JSON files")
	parser.add_argument('-a','--associated_data',type=str, help="directory of associated data")
	args = parser.parse_args()
	filepath = args.filepath
	target_dir = args.target_dir
	config_path = args.config


	autoCORPus(config_path, filepath, target_dir)