"""Main entry script for the autocorpus CLI."""

import argparse
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from . import add_file_logger, logger
from .autocorpus import Autocorpus
from .configs.default_config import DefaultConfig
from .inputs import read_file_structure
from .run import run_autocorpus

parser = argparse.ArgumentParser(prog="PROG")
parser.add_argument(
    "-f", "--filepath", type=str, help="filepath for document/directory to run AC on"
)
parser.add_argument(
    "-t", "--target_dir", type=str, help="target directory"
)  # default autoCORPusOutput
parser.add_argument(
    "-o",
    "--output_format",
    type=str,
    help=(
        "output format for main text, can be either JSON or XML. "
        "Does not effect tables or abbreviations"
    ),
)

group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-c", "--config", type=str, help="filepath for configuration JSON file"
)
group.add_argument(
    "-b", "--default_config", type=str, help="name of a default config file"
)


def main():
    """The main entrypoint for the Auto-CORPus CLI."""
    args = parser.parse_args()
    file_path = Path(args.filepath)
    target_dir = Path(args.target_dir if args.target_dir else "autoCORPus_output")
    config = args.config if args.config else args.default_config
    output_format = args.output_format if args.output_format else "JSON"

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
        f"{cdate.day}-{cdate.month}-{cdate.year}-{cdate.hour}-{cdate.minute}.log"
    )
    add_file_logger(log_file_path)

    logger.info(
        f"Auto-CORPus log file from {cdate.hour}:{cdate.minute} "
        f"on {cdate.day}/{cdate.month}/{cdate.year}"
    )
    logger.info(f"Input path: {file_path}")
    logger.info(f"Output path: {target_dir}")
    logger.info(f"Config: {config}")
    logger.info(f"Output format: {output_format}")

    if args.config:
        config = Autocorpus.read_config(args.config)
    elif args.default_config:
        try:
            config = DefaultConfig[args.default_config].load_config()
        except KeyError:
            raise ValueError(f"{args.default_config} is not a valid default config.")

    success = []
    errors = []
    for key in pbar:
        pbar.set_postfix(
            {
                "file": key + "*",
                "linked_tables": len(structure[key]["linked_tables"]),
            }
        )
        try:
            run_autocorpus(config, structure, key, output_format)
            success.append(f"{key} was processed successfully.")
        except Exception as e:
            errors.append(f"{key} failed due to {e}.")

    logger.info(f"{len(success)} files processed.")
    if errors:
        logger.error(f"{len(errors)} files not processed due to errors.")
    for msg in success:
        logger.info(msg)
    for msg in errors:
        logger.error(errors)

    if errors:
        logger.warning(
            "Auto-CORPus has completed processing with some errors. "
            "Please inspect the log file for further details."
        )


if __name__ == "__main__":
    main()
