"""Primary build test script used for regression testing between AC output versions."""

import json
from pathlib import Path
from typing import Any

from autocorpus.configs.default_config import DefaultConfig


def test_pmc_autocorpus():
    """A regression test for the main autoCORPus class, using the current PMC config on the AutoCORPus Paper.

    The test data output is built by running Auto-CORPus from the root of the repo with the
    following arguments
    ```
    auto-corpus -b "PMC" -t "tests/data/PMC/Current/" -f "tests/data/PMC/Current/PMC8885717.html"
    ```
    """
    from autocorpus.Autocorpus import Autocorpus

    pmc_example_path = data_path / "PMC" / "Current"
    with open(
        pmc_example_path / "PMC8885717_abbreviations.json",
    ) as f:
        expected_abbreviations = json.load(f)
    with open(
        Path(__file__).parent / "data" / "PMC" / "Current" / "PMC8885717_bioc.json",
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)
    with open(
        Path(__file__).parent / "data" / "PMC" / "Current" / "PMC8885717_tables.json",
        encoding="utf-8",
    ) as f:
        expected_tables = json.load(f)

    auto_corpus = Autocorpus(
        config=DefaultConfig.PMC.load_config(),
        base_dir="tests/data/PMC/Current",
        main_text="tests/data/PMC/Current/PMC8885717.html",
    )

    auto_corpus.process_files()

    abbreviations = auto_corpus.abbreviations
    bioc = auto_corpus.to_bioc()
    tables = auto_corpus.tables

    abbreviations.pop("date")
    expected_abbreviations.pop("date")
    assert abbreviations == expected_abbreviations
    bioc.pop("date")
    expected_bioc.pop("date")
    assert bioc == expected_bioc
    tables.pop("date")
    expected_tables.pop("date")
    assert tables == expected_tables


def test_legacy_pmc_autocorpus(data_path: Path):
    """A regression test for the main autoCORPus class, using the legacy PMC config on the AutoCORPus Paper.

    The test data output is built by running Auto-CORPus from the root of the repo with the
    following arguments:
    ```
    auto-corpus -b "LEGACY_PMC" -t "tests/data/PMC/Pre-Oct-2024/" -f "tests/data/PMC/Pre-Oct-2024/PMC8885717.html"
    ```
    """
    from autocorpus.Autocorpus import Autocorpus

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
