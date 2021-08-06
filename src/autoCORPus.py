import json
import sys
from bs4 import BeautifulSoup
import os
import pytest
import errno

def handle_path(func):
	def inner_function(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except IOError as io:
			print(io)
		except OSError as exc:
			print(exc)
		except Error as e:
			print(e)
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
	'''

	@handle_path
	def __read_config(self, config_path):
		with open(config_path, "r") as f:
			## TODO: validate config file here if possible
			return json.load(f)

	@handle_path
	def __import_file(self, file_path):
		with open(file_path, "r") as f:
			return f.read()

	@handle_path
	def __handle_target_dir(self, target_dir):
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)
		return target_dir

	def __init__(self, config_path, file_path, target_dir):
		self.file = self.__import_file(file_path)
		self.target_dir = self.__handle_target_dir(target_dir)
		self.config=self.__read_config(config_path)
		pass