"""Primary build test script used for regression testing between AC output versions."""

import json
from pathlib import Path
from typing import Any

import pytest

from autocorpus.config import DefaultConfig
from autocorpus.file_processing import process_file


@pytest.mark.parametrize(
    "input_file, config",
    [
        ("PMC/Pre-Oct-2024/PMC8885717.html", DefaultConfig.LEGACY_PMC.load_config()),
        ("PMC/Current/PMC8885717.html", DefaultConfig.PMC.load_config()),
    ],
)
def test_autocorpus(data_path: Path, input_file: str, config: dict[str, Any]) -> None:
    """A regression test for the main autoCORPus class.

    Uses each PMC config on the AutoCORPus Paper.
    """
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

    auto_corpus = process_file(config=config, file_path=pmc_example_path)

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


@pytest.mark.skip_ci_macos
@pytest.mark.parametrize(
    "input_file, config",
    [
        ("Supplementary/PDF/tp-10-08-2123-coif.pdf", DefaultConfig.PMC.load_config()),
    ],
)
def test_pdf_to_bioc(data_path: Path, input_file: str, config: dict[str, Any]) -> None:
    """Test the conversion of a PDF file to a BioC format."""
    pdf_path = data_path / input_file
    expected_output = pdf_path.parent / "Expected Output" / pdf_path.name
    with open(
        str(expected_output).replace(".pdf", ".pdf_bioc.json"),
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)

    with open(
        str(expected_output).replace(".pdf", ".pdf_tables.json"),
        encoding="utf-8",
    ) as f:
        expected_tables = json.load(f)

    auto_corpus = process_file(config=config, file_path=pdf_path)

    new_bioc = auto_corpus.main_text
    new_tables = auto_corpus.tables

    _make_reproducible(new_bioc, expected_bioc, new_tables, expected_tables)

    assert new_bioc == expected_bioc
    assert new_tables == expected_tables


def _make_reproducible(*data: dict[str, Any]) -> None:
    """Make output files reproducible by stripping dates and file paths."""
    for d in data:
        d.pop("date")
        for doc in d["documents"]:
            doc.pop("inputfile", None)
