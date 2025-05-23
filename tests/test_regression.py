"""Primary build test script used for regression testing between AC output versions."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from autocorpus.autocorpus import Autocorpus
from autocorpus.configs.default_config import DefaultConfig


@pytest.mark.parametrize(
    "input_file, config",
    [
        ("PMC/Pre-Oct-2024/PMC8885717.html", DefaultConfig.LEGACY_PMC.load_config()),
        ("PMC/Current/PMC8885717.html", DefaultConfig.PMC.load_config()),
    ],
)
def test_autocorpus(data_path: Path, input_file: str, config: dict[str, Any]) -> None:
    """A regression test for the main autoCORPus class, using the each PMC config on the AutoCORPus Paper."""
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
        main_text=pmc_example_path,
    )

    auto_corpus.process_file()

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
def test_pdf_to_bioc(
    data_path: Path, input_file: str, config: dict[str, Any], tmp_path: Path
) -> None:
    """Test the conversion of a PDF file to a BioC format using a temp directory."""
    # Original paths
    original_pdf_path = data_path / input_file
    expected_output_path = (
        original_pdf_path.parent / "Expected Output" / original_pdf_path.name
    )

    # Temp setup
    temp_input_dir = tmp_path / "input"
    temp_input_dir.mkdir()
    temp_pdf_path = temp_input_dir / original_pdf_path.name
    shutil.copy(original_pdf_path, temp_pdf_path)

    # Load expected outputs
    with open(
        str(expected_output_path).replace(".pdf", ".pdf_bioc.json"),
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)

    with open(
        str(expected_output_path).replace(".pdf", ".pdf_tables.json"),
        encoding="utf-8",
    ) as f:
        expected_tables = json.load(f)

    # Process in temp dir
    ac = Autocorpus(config=config)
    ac.process_files(files=[temp_pdf_path])

    # Load results
    with open(
        str(temp_pdf_path).replace(".pdf", ".pdf_bioc.json"),
        encoding="utf-8",
    ) as f:
        new_bioc = json.load(f)

    with open(
        str(temp_pdf_path).replace(".pdf", ".pdf_tables.json"),
        encoding="utf-8",
    ) as f:
        new_tables = json.load(f)

    _make_reproducible(new_bioc, expected_bioc, new_tables, expected_tables)

    assert new_bioc == expected_bioc
    assert new_tables == expected_tables


@pytest.mark.parametrize(
    "input_file, config, has_tables",
    [
        ("Supplementary/Word/mmc1.doc", DefaultConfig.PMC.load_config(), False),
    ],
)
def test_word_to_bioc(
    data_path: Path,
    input_file: str,
    config: dict[str, Any],
    has_tables: bool,
    tmp_path: Path,
) -> None:
    """Test the conversion of a doc file to a BioC format using a temp directory."""
    # Original file locations
    original_doc_path = data_path / input_file
    expected_output_path = (
        original_doc_path.parent / "Expected Output" / original_doc_path.name
    )

    # Copy the input doc file to the temp directory
    temp_input_dir = tmp_path / "input"
    temp_input_dir.mkdir()
    temp_doc_path = temp_input_dir / original_doc_path.name
    shutil.copy(original_doc_path, temp_doc_path)

    # Load expected BioC output
    with open(
        str(expected_output_path).replace(".doc", ".doc_bioc.json"),
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)

    ac = Autocorpus(config=config)
    ac.process_files(files=[temp_doc_path])  # Run on temp file

    # Load generated BioC output from temp dir
    with open(
        str(temp_doc_path).replace(".doc", ".doc_bioc.json"),
        encoding="utf-8",
    ) as f:
        new_bioc = json.load(f)

    if has_tables:
        with open(
            str(expected_output_path).replace(".doc", ".doc_tables.json"),
            encoding="utf-8",
        ) as f:
            expected_tables = json.load(f)

        with open(
            str(temp_doc_path).replace(".doc", ".doc_tables.json"),
            encoding="utf-8",
        ) as f:
            new_tables = json.load(f)

        _make_reproducible(new_bioc, expected_bioc, new_tables, expected_tables)
        assert new_tables == expected_tables
    else:
        _make_reproducible(new_bioc, expected_bioc)

    assert new_bioc == expected_bioc


def _make_reproducible(*data: dict[str, Any]) -> None:
    """Make output files reproducible by stripping dates and file paths."""
    for d in data:
        d.pop("date")
        for doc in d["documents"]:
            doc.pop("inputfile")
