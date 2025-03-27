"""AutoCorpus package."""

import logging
from importlib.metadata import version

__version__ = version(__name__)


def create_logger():
    """Create a logger for the program with default settings."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create console handler
    ch = logging.StreamHandler()
    ch.setFormatter(_log_formatter)

    # add the handlers to the logger
    logger.addHandler(ch)

    return logger


def add_file_logger(file_path):
    """Add a log handler to write log messages to file."""
    # same format as used for console
    fh = logging.FileHandler(file_path)
    fh.setFormatter(_log_formatter)
    logger.addHandler(fh)


_log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

logger = create_logger()
"""The logger for the Auto-CORPus module and command-line program."""
