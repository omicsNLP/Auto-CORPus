"""Contains a loader for default configuration files."""

import importlib.resources as resources
import json
from enum import Enum
from typing import Any


def read_config(config_path: str) -> dict[str, Any]:
    """Reads a configuration file and returns its content.

    Args:
        config_path: The path to the configuration file.

    Returns:
        dict: The content of the configuration file.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        json.JSONDecodeError: If the configuration file is not a valid JSON.
        KeyError: If the configuration file does not contain the expected "config" key.
    """
    with open(config_path, encoding="utf-8") as f:
        ## TODO: validate config file here if possible
        content = json.load(f)
        return content["config"]


class DefaultConfig(Enum):
    """An enumeration representing different configuration files for various datasets.

    Attributes:
            LEGACY_PMC: Configuration file for legacy PMC data (pre-October 2024).
            PMC: Configuration file for current PMC data.
            PLOS_GENETICS: Configuration file for PLOS Genetics data.
            NATURE_GENETICS: Configuration file for Nature Genetics data.

    Methods:
            load_config():
                Loads and returns the configuration from the associated file.
                The configuration is lazy-loaded and cached upon first access.

    """

    LEGACY_PMC = "config_pmc_pre_oct_2024.json"
    PMC = "config_pmc.json"
    PLOS_GENETICS = "config_plos_genetics.json"
    NATURE_GENETICS = "config_nature_genetics.json"

    def __init__(self, filename: str) -> None:
        """Initializes the DefaultConfig enum with the given filename.

        Args:
            filename: The name of the configuration file to load.
        """
        self._filename = filename
        self._config: dict[str, Any] = {}  # Lazy-loaded cache

    def load_config(self) -> dict[str, Any]:
        """Loads the configuration file when first accessed.

        Returns:
            The configuration file as a dictionary.
        """
        if self._config == {}:
            config_path = resources.files("autocorpus.configs") / self._filename
            with config_path.open("r", encoding="utf-8") as f_in:
                self._config = json.load(f_in)["config"]
        return self._config
