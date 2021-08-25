import argparse
import os

from autoCORPus import autoCORPus

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

if os.path.isdir(file_path):
	with open("references.csv", "w") as outfile:
		for file in os.listdir(file_path):
			if file.endswith(".html"):
				autoCORPus(config, f"{file_path}/{file}", associated_data).to_file(target_dir)
				# autoCORPus(config, f"{file_path}/{file}", associated_data).to_bioc(target_dir)
				#outfile.write(autoCORPus(config, f"{file_path}/{file}", associated_data).output_references() + "\n")

else:
	autoCORPus(config, file_path, associated_data).to_file(target_dir)

