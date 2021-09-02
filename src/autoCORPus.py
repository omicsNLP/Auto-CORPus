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
			return soup
		except Exception as e:
			print(e)

	def __clean_text(self, result):
		'''
		Tom's note

		This is no longer used, no need for it from what I can see but will leave it in just incase.


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

		# result['paragraphs'] = [
		# 	p for p in result['paragraphs'] if p['body'].replace('Go to:', '').strip() != '']
		return result


	def __get_keywords(self, soup, config):

		keywordSection = {
			"section_heading": "keywords",
			"subsection_heading": "",
			"body": soup.find(config["keywords"]["name"], config["keywords"]["attrs"]).get_text(),
			"section_type": [
				{
					"IAO_term": "keywords section",
					"IAO_id": "IAO:0000630"
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
			maintext.extend(section(config, sec, self.file_name).to_dict())
		# filter out the sections which do not contain any info
		filteredText = []
		[filteredText.append(x) for x in maintext if x]
		uniqueText = []
		for text in filteredText:
			if text not in uniqueText:
				uniqueText.append(text)
		pass



		result['paragraphs'] = self.__set_unknown_section_headings(uniqueText)

		# for para in result['paragraphs']:
		# 	if para['section_heading'] == "":
		# 		if para['section_type'] == []:
		# 			print(F"{self.file_name} does not have a section heading or section type")
		# 		else:
		# 			print(F"{self.file_name} has no section heading but a section type of {json.dumps(para['section_type'])}")
		# 	else:
		# 		if para['section_type'] == []:
		# 			print(F"{self.file_name} has a section heading of {para['section_heading']} but no section type")
		return result
		# return self.__clean_text(result)

	def __set_unknown_section_headings(self, uniqueText):
		paper = {}

		for para in uniqueText:
			paper[para['section_heading']] = [x['IAO_term'] for x in para['section_type']]
		mapping_dict_with_DAG = assgin_heading_by_DAG(paper)
		for i, para in enumerate(uniqueText):
			if para['section_heading'] in mapping_dict_with_DAG.keys():
				if para['section_type'] == []:
					uniqueText[i]['section_type'] = mapping_dict_with_DAG[para['section_heading']]
		return uniqueText
		pass

	def __init__(self, config_path, file_path, associated_data_path=None, outfile=None):
		self.file_name = file_path
		self.outfile = outfile
		self.temp_file = file_path.split("/")[-1]
		self.text, self.file_path = self.__import_file(file_path)
		self.config=self.__read_config(config_path)
		self.soup = self.__soupify_infile()
		self.main_text = self.__extract_text(self.soup, self.config)
		try:
			self.abbreviations = abbreviations(self.main_text, self.soup, self.config).to_dict()
		except Exception as e:
			self.abbreviations = {}
		self.tables = table(self.soup, self.config, self.file_name).to_dict()
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

	@handle_path
	def to_bioc(self, target_dir):
		file_name = self.file_path.split("/")[-1].replace(".html", "").strip()
		with open(target_dir + "/" + file_name + ".json", "w") as outfile:
			outfile.write(BiocFormatter(self).to_json(2))

	def output_references(self):
		return ""


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