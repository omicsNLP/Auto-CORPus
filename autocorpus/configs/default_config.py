import importlib.resources as resources
import json
from enum import Enum


class DefaultConfig(Enum):
    """DefaultConfig(Enum):
        An enumeration representing different configuration files for various datasets.

    Attributes:
            LEGACY_PMC (str): Configuration file for legacy PMC data (pre-October 2024).
            PMC (str): Configuration file for current PMC data.
            PLOS_GENETICS (str): Configuration file for PLOS Genetics data.
            NATURE_GENETICS (str): Configuration file for Nature Genetics data.

    Methods:
            load_config():
                Loads and returns the configuration from the associated file.
                The configuration is lazy-loaded and cached upon first access.
    """

    LEGACY_PMC = "config_pmc_pre_oct_2024.json"
    PMC = "config_pmc.json"
    PLOS_GENETICS = "config_plos_genetics.json"
    NATURE_GENETICS = "config_nature_genetics.json"

    def __init__(self, filename):
        """Initializes the DefaultConfig enum with the given filename.

        Args:
            filename (str): The name of the configuration file to load.
        """
        self._filename = filename
        self._config = None  # Lazy-loaded cache

    def load_config(self):
        """Loads the configuration file when first accessed."""
        if self._config is None:
            config_path = resources.files("autocorpus.configs") / self._filename
            with config_path.open("r", encoding="utf-8") as f_in:
                self._config = json.load(f_in)["config"]
        return self._config
