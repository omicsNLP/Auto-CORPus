import importlib.resources as resources
import json
from enum import Enum


class DefaultConfig(Enum):
    """DefaultConfig(Enum):
        An enumeration for default configuration files used in the Auto-CORPus project.

    Attributes:
            LEGACY_PMC (dict): Legacy PMC configuration (pre-October 2024).
            PMC (dict): Current PMC configuration.
            PLOS_GENETICS (dict): PLOS Genetics configuration.
            NATURE_GENETICS (dict): Nature Genetics configuration.
    """

    LEGACY_PMC = "config_pmc_pre_oct_2024.json"
    PMC = "config_pmc.json"
    PLOS_GENETICS = "config_plos_genetics.json"
    NATURE_GENETICS = "config_nature_genetics.json"

    def __init__(self, filename):
        self._filename = filename
        self._config = None  # Lazy-loaded cache

    def _load_config(self):
        """Loads the configuration file when first accessed."""
        if self._config is None:
            config_path = resources.files("autocorpus.configs") / self._filename
            with config_path.open("r", encoding="utf-8") as f_in:
                self._config = json.load(f_in)["config"]
        return self._config

    def __repr__(self):
        """Make the enum return the loaded config when accessed."""
        return repr(self._load_config())

    def __str__(self):
        """Make print(DefaultConfig.PMC) return the JSON content."""
        return str(self._load_config())

    def __getitem__(self, key):
        return self._load_config()[key]

    def __iter__(self):
        return iter(self._load_config())

    def keys(self):
        return self._load_config().keys()

    def values(self):
        return self._load_config().values()

    def items(self):
        return self._load_config().items()
