import json
from pathlib import Path


class DefaultConfig:
    """
    DefaultConfig class provides a way to initialize and load different configurations for the application.
    Attributes:
        LEGACY_PMC (int): Identifier for the legacy PMC configuration.
        PMC (int): Identifier for the PMC configuration.
        PLOS_GENETICS (int): Identifier for the PLOS Genetics configuration.
        NATURE_GENETICS (int): Identifier for the Nature Genetics configuration.
    Methods:
        string_to_constant(config_name: str) -> int:
                config (str): The configuration name to load.
        load_config(config: int) -> dict:
            Loads the specified configuration file.
                config (str): The constant id of the default configuration file to load.
            Returns:
                dict: The loaded configuration as a dictionary.
    """

    LEGACY_PMC = 1
    PMC = 2
    PLOS_GENETICS = 3
    NATURE_GENETICS = 4

    @staticmethod
    def string_to_constant(config_name:str) -> int:
        config_name = config_name.upper()
        if hasattr(DefaultConfig, config_name):
            return getattr(DefaultConfig, config_name)
        raise ValueError(f"Invalid default config name: {config_name}. Please check documentation for a list of default configs")


    @staticmethod
    def load_config(config:int) -> dict:
        if config == DefaultConfig.LEGACY_PMC:
            config_file = "config_pmc_pre_oct_2024.json"
        elif config == DefaultConfig.PMC:
            config_file = "config_pmc.json"
        elif config == DefaultConfig.PLOS_GENETICS:
            config_file = "config_plos_genetics.json"
        elif config == DefaultConfig.NATURE_GENETICS:
            config_file = "config_nature_genetics.json"
        else:
            raise Exception(
                "A valid config was not provided. Please provide a valid DefaultConfig setting."
            )

        config_path = Path(__file__).parent / config_file
        loaded_config = {}
        with open(config_path, encoding="utf-8") as f_in:
            loaded_config = json.load(f_in)
        return loaded_config["config"]
