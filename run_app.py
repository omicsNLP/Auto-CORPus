import argparse
import glob
import imghdr
import os
import re
from datetime import datetime
from os.path import exists

from tqdm import tqdm

from src.AutoCorpus import AutoCorpus
from supplementary_processor import supplementary_types


def get_file_type(f_path):
    """
    param file_path: file path to be checked
    :return: "directory", "main_text", "linked_table" or "table_image"
    """
    if os.path.isdir(f_path):
        return "directory"
    elif f_path.endswith(".html"):
        if re.search(r"table_\d+.html", f_path):
            return "linked_tables"
        else:
            return "main_text"
    elif imghdr.what(f_path):
        # imghdr returns the type of image a file is (png/jpeg etc. or None if not an image)
        # this should be tidied up to only include the image types which are supported by AC instead of any image files
        return "table_images"
    elif [f_path.endswith(x) for x in supplementary_types]:
        return "supplementary_files"
    else:
        print(F"unable to identify file type for {f_path}, file will not be processed")


def fill_structure(structure, key, ftype, fpath):
    """
    takes the structure dict, if key is not present then creates new entry
    with default vals and adds fpath to correct ftype
    if key is present then updates the dict with the new fpath only

    Args:
        structure: structure dict
        key: base file name
        ftype: file type (main_text, linked_table, table_image)
        fpath: full path to the file

    Returns:
        dict: updated structure dct
    """
    if key not in structure:
        structure[key] = {
            "main_text": "",
            "out_dir": "",
            "linked_tables": [],
            "table_images": [],
            "supplementary_files": []
        }
    if ftype == "main_text" or ftype == "out_dir":
        structure[key][ftype] = fpath
    else:
        structure[key][ftype].append(fpath)
    return structure
    pass


def read_file_structure(f_path, t_dir):
    """
    takes in any file structure (flat or nested) and groups files, returns a dict of files which are all related and
    the paths to each related file

    Args:
        f_path (str): file path string
        t_dir (str): directory URL string

    Returns:
        dict: dictionary
    """
    structure = {}
    if os.path.exists(f_path):
        omit_dir = "/".join(f_path.split("/"))
        if os.path.isdir(f_path):
            all_fpaths = sorted([x for x in glob.iglob(f_path + '/**', recursive=True)])
            # turn the 3d file structure into a flat 2d list of file paths
            for fpath in all_fpaths:
                tmp_out = fpath.replace(omit_dir, "")
                tmp_out = os.path.basename(os.path.dirname(tmp_out))
                out_dir = os.path.join(t_dir, tmp_out) if tmp_out else t_dir
                ftype = get_file_type(fpath)
                base_file = None
                if ftype == "directory":
                    continue
                elif ftype == "main_text":
                    base_file = re.sub(r"\.html", "", fpath)
                    structure = fill_structure(structure, base_file, 'main_text', fpath)
                    structure = fill_structure(structure, base_file, 'out_dir', out_dir)
                elif ftype == "linked_tables":
                    base_file = re.sub(r"_table_\d+\.html", "", fpath)
                    structure = fill_structure(structure, base_file, 'linked_tables', fpath)
                    structure = fill_structure(structure, base_file, 'out_dir', out_dir)
                elif ftype == "table_images":
                    base_file = re.sub(r"_table_\d+\..*", "", fpath)
                    structure = fill_structure(structure, base_file, 'table_images', fpath)
                    structure = fill_structure(structure, base_file, 'out_dir', out_dir)
                elif ftype == "supplementary_files":
                    base_file = re.sub(r"_supp_\d+\..*", "", fpath)
                    structure = fill_structure(structure, base_file, 'supplementary_files', fpath)
                    structure = fill_structure(structure, base_file, 'out_dir', out_dir)
                elif not ftype:
                    print(F"cannot determine file type for {fpath}, AC will not process this file")
                if base_file in structure:
                    structure = fill_structure(structure, base_file, 'out_dir', out_dir)
            return structure
        else:
            ftype = get_file_type(f_path)
            base_file = None
            if ftype == "main_text":
                base_file = re.sub(r"\.html", "", f_path).split("/")[-1]
            if ftype == "linked_tables":
                base_file = re.sub(r"_table_\d+\.html", "", f_path).split("/")[-1]
            if ftype == "table_images":
                base_file = re.sub(r"_table_\d+\..*", "", f_path).split("/")[-1]
            template = {
                base_file: {
                    "main_text": "",
                    "out_dir": t_dir,
                    "linked_tables": [],
                    "table_images": []
                }
            }
            template[base_file][get_file_type(f_path)] = f_path if get_file_type(f_path) == "main_text" else [
                f_path]
            return template
    else:
        print(F"{f_path} does not exist")
    pass


def main():
    parser = argparse.ArgumentParser(prog='PROG')
    parser.add_argument('-f', '--filepath', type=str, help="filepath for document/directory to run AC on")
    parser.add_argument('-t', '--target_dir', type=str, help="target directory")  # default autoCORPusOutput
    parser.add_argument('-o', '--output_format', type=str,
                        help="output format for main text, can be either JSON or XML. Does not effect tables or "
                             "abbreviations")
    parser.add_argument('-s', '--trained_data_set', type=str,
                        help="trained dataset to use with pytesseract, must be in the form pytesseract expects for the "
                             "lang argument, default eng")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--config", type=str, help="filepath for configuration JSON file")

    args = parser.parse_args()
    file_path = args.filepath
    if not exists(file_path):
        exit(F"Input file path does not exist: {file_path}")
    target_dir = args.target_dir if args.target_dir else "autoCORPus_output"

    structure = read_file_structure(file_path, target_dir)
    pbar = tqdm(structure.keys())
    cdate = datetime.now()

    config = args.config
    error_occurred = False
    output_format = args.output_format if args.output_format else "JSON"
    # trained_data = args.trained_data_set if args.output_format else "eng"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    log_file_name = F"{target_dir}/autoCORPus-log-{cdate.day}-{cdate.month}-{cdate.year}-{cdate.hour}-{cdate.minute}"

    with open(log_file_name, "w") as log_file:
        log_file.write(
            F"Auto-CORPus log file from {cdate.hour}:{cdate.minute} on {cdate.day}/{cdate.month}/{cdate.year}\n")
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
                    "table_images": len(structure[key]['table_images']),
                    "supplementary_files": len(structure[key]['supplementary_files'])
                }
            )
            if os.path.isdir(file_path):
                base_dir = file_path
            else:
                base_dir = "/".join(file_path.split("/")[:-1])
            try:
                ac = AutoCorpus(config, base_dir=base_dir, main_text=structure[key]['main_text'],
                                linked_tables=sorted(structure[key]['linked_tables']),
                                supplementary_files=sorted(structure[key]['supplementary_files']))

                out_dir = structure[key]['out_dir']
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)
                if structure[key]["main_text"] and ac.main_text:
                    key = key.replace('\\', '/')
                    if output_format.lower() == "json":
                        with open(out_dir + "/" + key.split("/")[-1] + "_bioc.json", "w", encoding='utf-8') as outfp:
                            outfp.write(ac.main_text_to_bioc_json())
                    else:
                        with open(out_dir + "/" + key.split("/")[-1] + "_bioc.xml", "w", encoding='utf-8') as outfp:
                            outfp.write(ac.main_text_to_bioc_xml())
                    with open(out_dir + "/" + key.split("/")[-1] + "_abbreviations.json", "w",
                              encoding='utf-8') as outfp:
                        outfp.write(ac.abbreviations_to_bioc_json())

                # AC does not support the conversion of tables or abbreviations to the XML format
                if ac.has_tables:
                    with open(out_dir + "/" + key.split("/")[-1] + "_tables.json", "w", encoding='utf-8') as outfp:
                        outfp.write(ac.tables_to_bioc_json())
                success.append(F"{key} was processed successfully.")
            except Exception as e:
                errors.append(F"{key} failed due to {e}.")
                error_occurred = True

        log_file.write(F"{len(success)} files processed.\n")
        log_file.write(F"{len(errors)} files not processed due to errors.\n\n\n")
        log_file.write("\n".join(success) + "\n")
        log_file.write("\n".join(errors) + "\n")
        if error_occurred:
            print(
                "Auto-CORPus has completed processing with some errors. Please inspect the log file for further "
                "details.")


if __name__ == "__main__":
    main()
