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
from src.bioc_formatter import BiocFormatter
from bioc import loads, dumps, BioCFileType

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
	'''
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
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)
		return

	def __validate_infile(self):
		pass

	def __soupify_infile(self, fpath):
		try:
			with open(fpath, "r") as fp:
				soup = BeautifulSoup(fp.read(), 'html.parser')
				for e in soup.find_all(attrs={'style': ['display:none', 'visibility:hidden']}):
					e.extract()
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
		idx_section = []
		section_headings = set([i['section_heading'] for i in result['paragraphs']])

		for i in range(len(section_headings)):
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
		return result


	def __get_keywords(self, soup, config):

		keywordSection = {
			"section_heading": "keywords",
			"subsection_heading": "",
			"body": soup.find(config["keywords"]["name"], config["keywords"]["attrs"]).get_text(),
			"section_type": [
				{
					"iao_name": "keywords section",
					"iao_id": "IAO:0000630"
				}
			]
		}
		return [keywordSection]

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
		body_select_tag = 'p,span,a'

		# Extract title
		try:
			h1 = soup.find(config['title']['name'],
			               config['title']['attrs']).get_text().strip('\n')
		except:
			h1 = ''
		result['title'] = h1
		if soup.find(config["keywords"]["name"], config["keywords"]["attrs"]):
			maintext = self.__get_keywords(soup, config)
		else:
			maintext = []
		sections = soup.find_all(config['sections']['name'], config['sections']['attrs'])
		for sec in sections:
			maintext.extend(section(config, sec).to_dict())
		# filter out the sections which do not contain any info
		filteredText = []
		[filteredText.append(x) for x in maintext if x]
		uniqueText = []
		for text in filteredText:
			if text not in uniqueText:
				uniqueText.append(text)

		result['paragraphs'] = self.__set_unknown_section_headings(uniqueText)

		return result

	def __set_unknown_section_headings(self, uniqueText):
		paper = {}
		for para in uniqueText:
			paper[para['section_heading']] = [x['iao_name'] for x in para['section_type']]
		mapping_dict_with_DAG = assgin_heading_by_DAG(paper)
		for i, para in enumerate(uniqueText):
			if para['section_heading'] in mapping_dict_with_DAG.keys():
				if para['section_type'] == []:
					uniqueText[i]['section_type'] = mapping_dict_with_DAG[para['section_heading']]
		return uniqueText

	def __handle_html(self, file_path, config):
		'''
		handles common HTML processing elements across main_text and linked_tables (creates soup and parses tables)
		:return: soup object
		'''
		self.file_name = file_path.split("/")[-1]
		soup = self.__soupify_infile(file_path)
		if self.tables == {}:
			self.tables = table(soup, config, file_path).to_dict()
		else:
			self.tables["documents"].extend(table(soup, config, file_path).to_dict()["documents"])
		return soup

	def __init__(self, config_path, main_text = None, linked_tables = None, table_images = None, associated_data_path=None):
		'''

		:param config_path: path to the config file to be used
		:param file_path: path to the main text of the article (HTML files only)
		:param linked_tables: list of linked table file paths to be included in this run (HTML files only)
		:param table_images: list of table image file paths to be included in this run (JPEG or PNG files only)
		:param associated_data_path: this still needs sorting
		'''
		# handle common
		config = self.__read_config(config_path)
		self.file_path = main_text
		self.main_text = {}
		self.tables={}
		self.abbreviations = {}
		self.has_tables = False

		# handle main_text
		if main_text:
			soup = self.__handle_html(main_text, config)
			self.main_text = self.__extract_text(soup, config)
			# try:
			self.abbreviations = abbreviations(self.main_text, soup, config, main_text).to_dict()
			# except Exception as e:
			# 	print(e)
			if not self.tables["documents"] == []:
				self.has_tables = True
		if linked_tables:
			for table_file in linked_tables:
				soup = self.__handle_html(table_file, config)
			if not self.tables["documents"] == []:
				self.has_tables = True
		if table_images:
			self.tables = table_image(table_images).to_dict()
			if not self.tables["documents"] == []:
				self.has_tables = True

	def to_bioc(self):
		return BiocFormatter(self).to_dict()

	def main_text_to_bioc_json(self, indent=2):
		return BiocFormatter(self).to_json(indent)

	def main_text_to_bioc_xml(self):
		collection = loads(BiocFormatter(self).to_json(2), BioCFileType.BIOC_JSON)
		return dumps(collection, BioCFileType.BIOC_XML)

	def tables_to_bioc_json(self, indent=2):
		return json.dumps(self.tables, ensure_ascii=False, indent=indent)

	def abbreviations_to_bioc_json(self, indent=2):
		return json.dumps(self.abbreviations, ensure_ascii=False, indent=indent)

	def to_json(self, indent=2):
		return json.dumps(to_dict(), ensure_ascii=False, indent=indent)

	def to_dict(self):
		return {
			"main_text": self.main_text,
			"abbreviations": self.abbreviations,
			"tables": self.tables
		}

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--filepath", type=str,
	                    help="filepath of html file to be processed")
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


	autoCORPus(config_path, filepath, target_dir).to_file(target_dir)