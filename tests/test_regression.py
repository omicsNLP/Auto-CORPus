"""Primary build test script used for regression testing between AC output versions."""

import json
from pathlib import Path
from typing import Any

from autocorpus.configs.default_config import DefaultConfig


def test_autocorpus(data_path: Path):
    """A regression test for the main Auto-CORPus class on the Auto-CORPus paper.

    The test data output is built by running Auto-CORPus from the root of the repo with the
    following arguments:

    ```
    auto-corpus -b LEGACY_PMC -t tests/data/PMC/Pre-Oct-2024/ -f tests/data/PMC/Pre-Oct-2024/PMC8885717.html
    ```
    """
    from autocorpus.autocorpus import Autocorpus

    pmc_example_path = data_path / "PMC" / "Pre-Oct-2024"
    with open(
        pmc_example_path / "PMC8885717_abbreviations.json",
    ) as f:
        expected_abbreviations = json.load(f)
    with open(
        pmc_example_path / "PMC8885717_bioc.json",
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)
    with open(
        pmc_example_path / "PMC8885717_tables.json",
        encoding="utf-8",
    ) as f:
        expected_tables = json.load(f)

    auto_corpus = Autocorpus(
        config=DefaultConfig.LEGACY_PMC.load_config(),
        base_dir=str(pmc_example_path),
        main_text=str(pmc_example_path / "PMC8885717.html"),
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
