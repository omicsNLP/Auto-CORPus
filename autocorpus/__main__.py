"""Main entry script for the autocorpus CLI."""

import argparse
import re
from datetime import datetime
from pathlib import Path

from filetype import is_image
from tqdm import tqdm

from autocorpus.Autocorpus import Autocorpus

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
    help=(
        "output format for main text, can be either JSON or XML. "
        "Does not effect tables or abbreviations"
    ),
)
parser.add_argument(
    "-s",
    "--trained_data_set",
    type=str,
    help=(
        "trained dataset to use with pytesseract, must be in the form pytesseract "
        "expects for the lang argument, default eng"
    ),
)

group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-c", "--config", type=str, help="filepath for configuration JSON file"
)
group.add_argument(
    "-d", "--config_dir", type=str, help="directory of configuration JSON files"
)


def get_file_type(file_path: Path) -> str:
    """Identify the type of files present in the given path.

    :param file_path: file path to be checked
    :return: "directory", "main_text", "linked_table" or "table_image"
    """
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
    print(f"unable to identify file type for {file_path}, file will not be processed")
    return ""


def fill_structure(structure, key, ftype, fpath: Path):
    """Takes the structure dict, if key is not present then creates new entry with default vals and adds fpath to correct ftype if key is present then updates the dict with the new fpath only.

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
        structure[key][ftype] = str(fpath)
    else:
        structure[key][ftype].append(str(fpath))
    return structure


def read_file_structure(file_path: Path, target_dir: Path):
    """Takes in any file structure (flat or nested) and groups files, returns a dict of files which are all related and the paths to each related file.

    :param file_path:
    :param target_dir:
    :return: list of dicts
    """
    if file_path.is_dir():
        structure = {}
        all_fpaths = file_path.rglob("*")
        for fpath in all_fpaths:
            tmp_out = fpath.relative_to(file_path).parent
            out_dir = target_dir / tmp_out
            ftype = get_file_type(fpath)
            base_file = None
            if ftype == "directory":
                continue
            elif ftype == "main_text":
                base_file = re.sub(r"\.html", "", str(fpath))
                structure = fill_structure(structure, base_file, "main_text", fpath)
                structure = fill_structure(structure, base_file, "out_dir", out_dir)
            elif ftype == "linked_tables":
                base_file = re.sub(r"_table_\d+\.html", "", str(fpath))
                structure = fill_structure(structure, base_file, "linked_tables", fpath)
                structure = fill_structure(structure, base_file, "out_dir", out_dir)
            elif ftype == "table_images":
                base_file = re.sub(r"_table_\d+\..*", "", str(fpath))
                structure = fill_structure(structure, base_file, "table_images", fpath)
                structure = fill_structure(structure, base_file, "out_dir", out_dir)
            elif not ftype:
                print(
                    f"cannot determine file type for {fpath}. "
                    "AC will not process this file"
                )
            if base_file in structure:
                structure = fill_structure(structure, base_file, "out_dir", out_dir)
        return structure

    ftype = get_file_type(file_path)
    if ftype == "main_text":
        base_file = re.sub(r"\.html", "", str(file_path)).split("/")[-1]
    if ftype == "linked_tables":
        base_file = re.sub(r"_table_\d+\.html", "", str(file_path)).split("/")[-1]
    if ftype == "table_images":
        base_file = re.sub(r"_table_\d+\..*", "", str(file_path)).split("/")[-1]
    if not ftype:
        raise OSError(
            f"cannot determine file type for {file_path}. AC will not process this file"
        )
    template = {
        base_file: {
            "main_text": "",
            "out_dir": str(target_dir),
            "linked_tables": [],
            "table_images": [],
        }
    }
    template[base_file][get_file_type(file_path)] = str(
        file_path if get_file_type(file_path) == "main_text" else [file_path]
    )
    return template


def main():
    """The main entrypoint for the Auto-CORPus CLI."""
    args = parser.parse_args()
    file_path = Path(args.filepath)
    target_dir = Path(args.target_dir if args.target_dir else "autoCORPus_output")
    config = args.config
    config_dir = args.config_dir  # noqa: F841 ## TODO: Use this variable
    associated_data = args.associated_data  # noqa: F841 ## TODO: Use this variable
    output_format = args.output_format if args.output_format else "JSON"
    trained_data = args.trained_data_set if args.output_format else "eng"

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist")
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
    if not target_dir.is_dir():
        raise NotADirectoryError(f"{target_dir} is not a directory")

    structure = read_file_structure(file_path, target_dir)
    pbar = tqdm(structure.keys())
    cdate = datetime.now()

    log_file_path = (
        target_dir / "autoCORPus-log-"
        f"{cdate.day}-{cdate.month}-{cdate.year}-{cdate.hour}-{cdate.minute}"
    )

    with log_file_path.open("w") as log_file:
        log_file.write(
            f"Auto-CORPus log file from {cdate.hour}:{cdate.minute} "
            f"on {cdate.day}/{cdate.month}/{cdate.year}\n"
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
            base_dir = file_path.parent if not file_path.is_dir() else file_path
            try:
                ac = Autocorpus(
                    config,
                    base_dir=str(base_dir),
                    main_text=structure[key]["main_text"],
                    linked_tables=sorted(structure[key]["linked_tables"]),
                    table_images=sorted(structure[key]["table_images"]),
                    trained_data=trained_data,
                )

                out_dir = Path(structure[key]["out_dir"])
                if structure[key]["main_text"]:
                    key = key.replace("\\", "/")
                    if output_format.lower() == "json":
                        with open(
                            out_dir / f"{Path(key).name}_bioc.json",
                            "w",
                            encoding="utf-8",
                        ) as outfp:
                            outfp.write(ac.main_text_to_bioc_json())
                    else:
                        with open(
                            out_dir / f"{Path(key).name}_bioc.xml",
                            "w",
                            encoding="utf-8",
                        ) as outfp:
                            outfp.write(ac.main_text_to_bioc_xml())
                    with open(
                        out_dir / f"{Path(key).name}_abbreviations.json",
                        "w",
                        encoding="utf-8",
                    ) as outfp:
                        outfp.write(ac.abbreviations_to_bioc_json())

                # AC does not support the conversion of tables or abbreviations to XML
                if ac.has_tables:
                    with open(
                        out_dir / f"{Path(key).name}_tables.json", "w", encoding="utf-8"
                    ) as outfp:
                        outfp.write(ac.tables_to_bioc_json())
                success.append(f"{key} was processed successfully.")
            except Exception as e:
                errors.append(f"{key} failed due to {e}.")

        log_file.write(f"{len(success)} files processed.\n")
        log_file.write(f"{len(errors)} files not processed due to errors.\n\n\n")
        log_file.write("\n".join(success) + "\n")
        log_file.write("\n".join(errors) + "\n")
        if errors:
            print(
                "Auto-CORPus has completed processing with some errors. "
                "Please inspect the log file for further details."
            )


if __name__ == "__main__":
    main()
