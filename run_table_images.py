import argparse
import json
import os
from tqdm import tqdm
import glob
from src.table_image import table_image

from autoCORPus import autoCORPus

def handle_target_dir(target_dir):
	try:
		dirs = target_dir.split("/")[:-1]
		target = "/".join(dirs)
		os.makedirs(target)
	except:
		return

parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('-f','--filepath',type=str, help="filepath for base HTML document")
parser.add_argument('-t','--target_dir',type=str, help="target directory")
parser.add_argument('-a','--associated_data',type=str, help="directory of associated data")

group = parser.add_mutually_exclusive_group()
group.add_argument("-c", "--config", type=str, help="filepath for configuration JSON file")
group.add_argument("-d", "--config_dir", type=str, help="directory of configuration JSON files")


args = parser.parse_args()
file_path = args.filepath
target_dir = args.target_dir
config = args.config
config_dir = args.config_dir
associated_data = args.associated_data

files = []

if os.path.isdir(file_path):
	for filename in glob.iglob(file_path + '**/**', recursive=True):
		if os.path.isdir(filename):
			continue
		else:
			print(filename)
			files.append(filename)
else:
	print(F"single file {file_path}")

for file in tqdm(files):
	if file.endswith(".html"):
		autoCORPus(config, file, associated_data).to_file(target_dir)
	else:
		outfile = F"{file.replace(file.split('.')[-1], 'json')}"
		outfile = outfile.replace(outfile.split("/")[0], target_dir)
		handle_target_dir(outfile)
		with open(outfile, "w") as out:
			json.dump(table_image(file).to_dict(), out, ensure_ascii=False, indent=2)



