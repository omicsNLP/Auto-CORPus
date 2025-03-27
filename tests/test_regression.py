"""Primary build test script used for regression testing between AC output versions."""

import json
from pathlib import Path
from typing import Any

import pytest

from autocorpus.configs.default_config import DefaultConfig


@pytest.mark.parametrize(
    "input_file, config",
    [
        ("PMC/Pre-Oct-2024/PMC8885717.html", DefaultConfig.LEGACY_PMC.load_config()),
        ("PMC/Current/PMC8885717.html", DefaultConfig.PMC.load_config()),
    ],
)
def test_autocorpus(data_path: Path, input_file: Path, config: dict):
    """A regression test for the main autoCORPus class, using the each PMC config on the AutoCORPus Paper.

    The test data output is built by running Auto-CORPus from the root of the repo with the
    following arguments:
    ```
    auto-corpus -b "LEGACY_PMC" -t "tests/data/PMC/Pre-Oct-2024/" -f "tests/data/PMC/Pre-Oct-2024/PMC8885717.html"
    ```
    """
    from autocorpus.Autocorpus import Autocorpus

    pmc_example_path = data_path / input_file
    with open(
        str(pmc_example_path).replace(".html", "_abbreviations.json"), encoding="utf-8"
    ) as f:
        expected_abbreviations = json.load(f)
    with open(
        str(pmc_example_path).replace(".html", "_bioc.json"),
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)
    with open(
        str(pmc_example_path).replace(".html", "_tables.json"),
        encoding="utf-8",
    ) as f:
        expected_tables = json.load(f)

    auto_corpus = Autocorpus(
        config=config,
        base_dir=str(pmc_example_path),
        main_text=str(pmc_example_path),
    )

    auto_corpus.process_files()

    abbreviations = auto_corpus.abbreviations
    bioc = auto_corpus.to_bioc()
    tables = auto_corpus.tables

    _make_reproducible(
        abbreviations,
        expected_abbreviations,
        bioc,
        expected_bioc,
        tables,
        expected_tables,
    )
    assert abbreviations == expected_abbreviations
    assert bioc == expected_bioc
    assert tables == expected_tables


def _make_reproducible(*data: dict[str, Any]) -> None:
    """Make output files reproducible by stripping dates and file paths."""
    for d in data:
        d.pop("date")
        for doc in d["documents"]:
            doc.pop("inputfile")
