import argparse
import os
import glob
from tqdm import tqdm
import re
import imghdr
from datetime import date, datetime

from src.autoCORPus import autoCORPus

parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('-f','--filepath',type=str, help="filepath for document/directory to run AC on")
parser.add_argument('-t','--target_dir',type=str, help="target directory") #default autoCORPusOutput
parser.add_argument('-a','--associated_data',type=str, help="directory of associated data")
parser.add_argument('-o','--output_format',type=str, help="output format for main text, can be either JSON or XML. Does not effect tables or abbreviations")
parser.add_argument('-s','--trained_data_set',type=str, help="trained dataset to use with pytesseract, must be in the form pytesseract expects for the lang argument, default eng")


group = parser.add_mutually_exclusive_group()
group.add_argument("-c", "--config", type=str, help="filepath for configuration JSON file")
group.add_argument("-d", "--config_dir", type=str, help="directory of configuration JSON files")


args = parser.parse_args()
file_path = args.filepath
target_dir = args.target_dir if args.target_dir else "autoCORPus_output"
config = args.config
config_dir = args.config_dir
associated_data = args.associated_data
output_format = args.output_format if args.output_format else "JSON"
trained_data = args.trained_data_set if args.output_format else "eng"

def get_file_type(file_path):
	'''
	:param file_path: file path to be checked
	:return: "directory", "main_text", "linked_table" or "table_image"
	'''
	if os.path.isdir(file_path):
		return("directory")
	elif file_path.endswith(".html"):
		if re.search("table_\d+.html", file_path):
			return("linked_tables")
		else:
			return("main_text")
	elif imghdr.what(file_path):
		# imghdr returns the type of image a file is (png/jpeg etc or None if not an image)
		# this should be tidied up to only include the image types which are supported by AC instead of any image files
		return("table_images")
	else:
		print(F"unable to identify file type for {file_path}, file will not be processed")

def fill_structure(structure, key, ftype, fpath):
	'''
	takes the structure dict, if key is not present then creates new entry with default vals and adds fpath to correct ftype
	if key is present then updates the dict with the new fpath only

	:param structure: structure dict
	:param key: base file name
	:param ftype: file type (main_text, linked_table, table_image
	:param fpath: full path to the file
	:return: updated structure dct
	'''
	if key not in structure:
		structure[key] = {
			"main_text": "",
			"out_dir": "",
			"linked_tables": [],
			"table_images": [],
		}
	if ftype == "main_text" or ftype == "out_dir":
		structure[key][ftype] = fpath
	else:
		structure[key][ftype].append(fpath)
	return structure
	pass

def read_file_structure(file_path, target_dir):
	'''
	takes in any file structure (flat or nested) and groups files, returns a dict of files which are all related and
	the paths to each related file
	:param file_path:
	:return: list of dicts
	'''
	structure = {}
	if os.path.exists(file_path):
		omit_dir = "/".join(file_path.split("/"))
		if os.path.isdir(file_path):
			all_fpaths = glob.iglob(file_path + '/**', recursive=True)
			# turn the 3d file structure into a flat 2d list of file paths
			for fpath in all_fpaths:
				tmp_out = fpath.replace(omit_dir, "")
				tmp_out = "/".join(tmp_out.split("/")[:-1])
				out_dir = target_dir + tmp_out
				ftype = get_file_type(fpath)
				if ftype == "directory":
					continue
				elif ftype == "main_text":
					base_file = re.sub("\.html", "", fpath)
					structure = fill_structure(structure, base_file, 'main_text', fpath)
					structure = fill_structure(structure, base_file, 'out_dir', out_dir)
				elif ftype == "linked_tables":
					base_file = re.sub("_table_\d+\.html", "", fpath)
					structure = fill_structure(structure, base_file, 'linked_tables', fpath)
					structure = fill_structure(structure, base_file, 'out_dir', out_dir)
				elif ftype == "table_images":
					base_file=re.sub("_table_\d+\..*", "", fpath)
					structure = fill_structure(structure, base_file, 'table_images', fpath)
					structure = fill_structure(structure, base_file, 'out_dir', out_dir)
				elif not ftype:
					print(F"cannot determine file type for {fpath}, AC will not process this file")
				if base_file in structure:
					structure = fill_structure(structure, base_file, 'out_dir', out_dir)
			return(structure)
		else:
			ftype = get_file_type(file_path)
			if ftype == "main_text":
				base_file = re.sub("\.html", "", file_path).split("/")[-1]
			if ftype == "linked_tables":
				base_file = re.sub("_table_\d+\.html", "", file_path).split("/")[-1]
			if ftype == "table_images":
				base_file=re.sub("_table_\d+\..*", "", file_path).split("/")[-1]
			template = {
				base_file: {
					"main_text": "",
					"out_dir": target_dir,
					"linked_tables": [],
					"table_images": []
				}
			}
			template[base_file][get_file_type(file_path)] = file_path if get_file_type(file_path) == "main_text" else [file_path]
			return template
	else:
		print(F"{file_path} does not exist")
	pass

structure = read_file_structure(file_path, target_dir)
pbar = tqdm(structure.keys())
cdate = datetime.now()

config = args.config
config_dir = args.config_dir
associated_data = args.associated_data
output_format = args.output_format if args.output_format else "JSON"
trained_data = args.trained_data_set if args.output_format else "eng"

logFileName = F"autoCORPus-log-{cdate.day}-{cdate.month}-{cdate.year}-{cdate.hour}-{cdate.minute}"
with open(logFileName, "w") as log_file:
	log_file.write(F"Auto-CORPus log file from {cdate.hour}:{cdate.minute} on {cdate.day}/{cdate.month}/{cdate.year}\n")
	log_file.write(F"Input directory provided: {file_path}\n")
	log_file.write(F"Output directory provided: {target_dir}\n")
	log_file.write(F"Config provided: {config}\n")
	log_file.write(F"Output format: {output_format}\n")
	success = []
	errors = []
	for key in pbar:
		pbar.set_postfix(
			{
				"file": key + "*",
				"linked_tables": len(structure[key]['linked_tables']),
				"table_images": len(structure[key]['table_images'])
			}
		)
		if os.path.isdir(file_path):
			base_dir = file_path
		else:
			base_dir = "/".join(file_path.split("/")[:-1])
		try:
			AC = autoCORPus(config, base_dir=base_dir, main_text=structure[key]['main_text'], linked_tables=sorted(structure[key]['linked_tables']), table_images=sorted(structure[key]['table_images']), trainedData=trained_data)

			out_dir = structure[key]['out_dir']

			if not os.path.exists(out_dir):
				os.makedirs(out_dir)
			if structure[key]["main_text"]:
				key = key.replace('\\','/')
				if output_format == "JSON":
					with open(out_dir + "/" + key.split("/")[-1] + "_bioc.json", "w", encoding='utf-8') as outfp:
						outfp.write(AC.main_text_to_bioc_json())
				else:
					with open(out_dir + "/" + key.split("/")[-1] + "_bioc.xml", "w", encoding='utf-8') as outfp:
						outfp.write(AC.main_text_to_bioc_xml())
				with open(out_dir + "/" + key.split("/")[-1] + "_abbreviations.json", "w", encoding='utf-8') as outfp:
					outfp.write(AC.abbreviations_to_bioc_json())

			# AC does not support the conversion of tables or abbreviations to the XML format
			if AC.has_tables:
				with open(out_dir + "/" + key.split("/")[-1] + "_tables.json", "w", encoding='utf-8') as outfp:
					outfp.write(AC.tables_to_bioc_json())
			success.append(F"{key} was processed successfully.")
		except Exception as e:
			errors.append(F"{key} failed due to {e}.")

	log_file.write(F"{len(success)} files processed.\n")
	log_file.write(F"{len(errors)} files not processed due to errors.\n\n\n")
	log_file.write("\n".join(success) + "\n")
	log_file.write("\n".join(errors) + "\n")



