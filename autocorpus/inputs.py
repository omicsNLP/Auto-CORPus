"""Module for processing the structure of the autocorpus input files."""

import re
from pathlib import Path
from typing import Any

from . import logger


def get_file_type(file_path: Path) -> str:
    """Identify the type of files present in the given path.

    Args:
        file_path: file path to be checked

    Returns:
        "directory", "main_text" or "linked_table"
    """
    if file_path.is_dir():
        return "directory"
    if file_path.suffix == ".html":
        if file_path.name.startswith("table_"):
            return "linked_tables"
        return "main_text"

    logger.warning(
        f"unable to identify file type for {file_path}, file will not be processed"
    )
    return ""


def fill_structure(structure, key, ftype, fpath: Path):
    """Update the structure dict to contain the correct structure.

    Takes the structure dict, if key is not present then creates new entry with default
    values. It then adds `fpath` to the correct `ftype`.

    Args:
        structure: structure dict
        key: base file name
        ftype: file type (main_text, linked_table)
        fpath: full path to the file

    Returns:
        The updated structure dictionary
    """
    if key not in structure:
        structure[key] = {
            "main_text": "",
            "out_dir": "",
            "linked_tables": [],
        }
    if ftype == "main_text" or ftype == "out_dir":
        structure[key][ftype] = str(fpath)
    else:
        structure[key][ftype].append(str(fpath))
    return structure


def read_file_structure(file_path: Path, target_dir: Path) -> dict[str, Any]:
    """Takes in any file structure (flat or nested) and groups files.

    Returns a dict of files which are all related and the paths to each related file.

    Args:
        file_path: path to the file or directory
        target_dir: path to the target directory

    Returns:
        Dictionary of files which are all related and the paths to each related file
    """
    if file_path.is_dir():
        structure: dict[str, Any] = {}
        all_fpaths = file_path.rglob("*")
        for fpath in all_fpaths:
            tmp_out = fpath.relative_to(file_path).parent
            out_dir = target_dir / tmp_out
            ftype = get_file_type(fpath)
            base_file = ""
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
            elif not ftype:
                logger.warning(
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
    if not ftype:
        raise OSError(
            f"cannot determine file type for {file_path}. AC will not process this file"
        )
    template = {
        base_file: {
            "main_text": "",
            "out_dir": str(target_dir),
            "linked_tables": [],
        }
    }
    template[base_file][get_file_type(file_path)] = str(
        file_path if get_file_type(file_path) == "main_text" else [file_path]
    )
    return template
