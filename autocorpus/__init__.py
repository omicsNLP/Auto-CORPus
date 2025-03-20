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

    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(ch)

    return logger


logger = create_logger()
"""The logger for the Auto-CORPus module and command-line program."""
