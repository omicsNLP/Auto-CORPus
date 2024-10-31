import argparse
import re
from datetime import datetime
from pathlib import Path

from filetype import is_image
from tqdm import tqdm

from autocorpus.autoCORPus import autoCORPus

parser = argparse.ArgumentParser(prog="PROG")
parser.add_argument(
    "-f", "--filepath", type=str, help="filepath for document/directory to run AC on"
)
parser.add_argument(
    "-t", "--target_dir", type=str, help="target directory"
)  # default autoCORPusOutput
parser.add_argument(
    "-a", "--associated_data", type=str, help="directory of associated data"
)
parser.add_argument(
    "-o",
    "--output_format",
    type=str,
    help="output format for main text, can be either JSON or XML. Does not effect tables or abbreviations",
)
parser.add_argument(
    "-s",
    "--trained_data_set",
    type=str,
    help="trained dataset to use with pytesseract, must be in the form pytesseract expects for the lang argument, default eng",
)

group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-c", "--config", type=str, help="filepath for configuration JSON file"
)
group.add_argument(
    "-d", "--config_dir", type=str, help="directory of configuration JSON files"
)

args = parser.parse_args()
file_path = args.filepath
target_dir = args.target_dir if args.target_dir else "autoCORPus_output"
config = args.config
config_dir = args.config_dir
associated_data = args.associated_data
output_format = args.output_format if args.output_format else "JSON"
trained_data = args.trained_data_set if args.output_format else "eng"


def get_file_type(file_path):
    """
    :param file_path: file path to be checked
    :return: "directory", "main_text", "linked_table" or "table_image"
    """
    file_path = Path(file_path)
    if file_path.is_dir():
        return "directory"
    elif file_path.suffix == ".html":
        if re.search(r"table_\d+.html", file_path.name):
            return "linked_tables"
        else:
            return "main_text"
    elif is_image(file_path):
        # this should be tidied up to only include the image types which are supported
        # by AC instead of any image files
        return "table_images"
    else:
        print(
            f"unable to identify file type for {file_path}, file will not be processed"
        )


def fill_structure(structure, key, ftype, fpath):
    """
    takes the structure dict, if key is not present then creates new entry with default vals and adds fpath to correct ftype
    if key is present then updates the dict with the new fpath only

    :param structure: structure dict
    :param key: base file name
    :param ftype: file type (main_text, linked_table, table_image
    :param fpath: full path to the file
    :return: updated structure dct
    """
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
    """
    takes in any file structure (flat or nested) and groups files, returns a dict of files which are all related and
    the paths to each related file
    :param file_path:
    :return: list of dicts
    """
    structure = {}
    file_path = Path(file_path)
    if file_path.exists():
        if file_path.is_dir():
            all_fpaths = file_path.rglob("*")
            for fpath in all_fpaths:
                tmp_out = fpath.relative_to(file_path).parent
                out_dir = Path(target_dir) / tmp_out
                ftype = get_file_type(fpath)
                base_file = None
                if ftype == "directory":
                    continue
                elif ftype == "main_text":
                    base_file = re.sub(r"\.html", "", fpath)
                    structure = fill_structure(structure, base_file, "main_text", fpath)
                    structure = fill_structure(structure, base_file, "out_dir", out_dir)
                elif ftype == "linked_tables":
                    base_file = re.sub(r"_table_\d+\.html", "", fpath)
                    structure = fill_structure(
                        structure, base_file, "linked_tables", fpath
                    )
                    structure = fill_structure(structure, base_file, "out_dir", out_dir)
                elif ftype == "table_images":
                    base_file = re.sub(r"_table_\d+\..*", "", fpath)
                    structure = fill_structure(
                        structure, base_file, "table_images", fpath
                    )
                    structure = fill_structure(structure, base_file, "out_dir", out_dir)
                elif not ftype:
                    print(
                        f"cannot determine file type for {fpath}, AC will not process this file"
                    )
                if base_file in structure:
                    structure = fill_structure(structure, base_file, "out_dir", out_dir)
            return structure
        else:
            ftype = get_file_type(file_path)
            if ftype == "main_text":
                base_file = re.sub(r"\.html", "", file_path).split("/")[-1]
            if ftype == "linked_tables":
                base_file = re.sub(r"_table_\d+\.html", "", file_path).split("/")[-1]
            if ftype == "table_images":
                base_file = re.sub(r"_table_\d+\..*", "", file_path).split("/")[-1]
            template = {
                base_file: {
                    "main_text": "",
                    "out_dir": target_dir,
                    "linked_tables": [],
                    "table_images": [],
                }
            }
            template[base_file][get_file_type(file_path)] = (
                file_path if get_file_type(file_path) == "main_text" else [file_path]
            )
            return template
    else:
        print(f"{file_path} does not exist")
    pass


structure = read_file_structure(file_path, target_dir)
pbar = tqdm(structure.keys())
cdate = datetime.now()

config = args.config
config_dir = args.config_dir
associated_data = args.associated_data
error_occurred = False
output_format = args.output_format if args.output_format else "JSON"
trained_data = args.trained_data_set if args.output_format else "eng"
target_dir = Path(target_dir)
if not target_dir.exists():
    target_dir.mkdir(parents=True)
logFileName = (
    target_dir
    / f"autoCORPus-log-{cdate.day}-{cdate.month}-{cdate.year}-{cdate.hour}-{cdate.minute}"
)

with logFileName.open("w") as log_file:
    log_file.write(
        f"Auto-CORPus log file from {cdate.hour}:{cdate.minute} on {cdate.day}/{cdate.month}/{cdate.year}\n"
    )
    log_file.write(f"Input directory provided: {file_path}\n")
    log_file.write(f"Output directory provided: {target_dir}\n")
    log_file.write(f"Config provided: {config}\n")
    log_file.write(f"Output format: {output_format}\n")
    success = []
    errors = []
    for key in pbar:
        pbar.set_postfix(
            {
                "file": key + "*",
                "linked_tables": len(structure[key]["linked_tables"]),
                "table_images": len(structure[key]["table_images"]),
            }
        )
        base_dir = (
            Path(file_path).parent if not Path(file_path).is_dir() else Path(file_path)
        )
        try:
            AC = autoCORPus(
                config,
                base_dir=base_dir,
                main_text=structure[key]["main_text"],
                linked_tables=sorted(structure[key]["linked_tables"]),
                table_images=sorted(structure[key]["table_images"]),
                trainedData=trained_data,
            )

            out_dir = Path(structure[key]["out_dir"])
            if structure[key]["main_text"]:
                key = key.replace("\\", "/")
                if output_format.lower() == "json":
                    with open(
                        out_dir / f"{Path(key).name}_bioc.json", "w", encoding="utf-8"
                    ) as outfp:
                        outfp.write(AC.main_text_to_bioc_json())
                else:
                    with open(
                        out_dir / f"{Path(key).name}_bioc.xml", "w", encoding="utf-8"
                    ) as outfp:
                        outfp.write(AC.main_text_to_bioc_xml())
                with open(
                    out_dir / f"{Path(key).name}_abbreviations.json",
                    "w",
                    encoding="utf-8",
                ) as outfp:
                    outfp.write(AC.abbreviations_to_bioc_json())

            # AC does not support the conversion of tables or abbreviations to the XML format
            if AC.has_tables:
                with open(
                    out_dir / f"{Path(key).name}_tables.json", "w", encoding="utf-8"
                ) as outfp:
                    outfp.write(AC.tables_to_bioc_json())
            success.append(f"{key} was processed successfully.")
        except Exception as e:
            errors.append(f"{key} failed due to {e}.")
            error_occurred = True

    log_file.write(f"{len(success)} files processed.\n")
    log_file.write(f"{len(errors)} files not processed due to errors.\n\n\n")
    log_file.write("\n".join(success) + "\n")
    log_file.write("\n".join(errors) + "\n")
    if error_occurred:
        print(
            "Auto-CORPus has completed processing with some errors. Please inspect the log file for further details."
        )
