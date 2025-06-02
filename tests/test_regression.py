"""Primary build test script used for regression testing between AC output versions."""

import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

from autocorpus.config import DefaultConfig
from autocorpus.file_processing import process_file

from .conftest import DATA_PATH


def _get_html_test_data_paths(subfolder: str):
    """Return paths to HTML test data files with appropriate DefaultConfig."""
    HTML_DATA_PATH = DATA_PATH / subfolder / "html"
    if not HTML_DATA_PATH.exists():
        return

    for dir_name in os.listdir(HTML_DATA_PATH):
        dir_path = HTML_DATA_PATH / dir_name
        if dir_path.is_dir():
            # Assume the folder name corresponds to a DefaultConfig
            config = getattr(DefaultConfig, dir_name).load_config()

            for file_path in dir_path.glob("*.html"):
                # The reason for converting the path to a string is so that we get the
                # file path in the test name (paths don't work for some reason)
                yield (str(file_path.relative_to(DATA_PATH)), config)


_private_test_data = list(_get_html_test_data_paths("private"))


@pytest.mark.parametrize(
    "input_file,config",
    _get_html_test_data_paths("public"),
)
def test_regression_html_public(
    data_path: Path, input_file: str, config: dict[str, Any]
) -> None:
    """Regression test for public HTML data."""
    _run_html_regression_test(data_path, input_file, config)


@pytest.mark.skipif(not _private_test_data, reason="Private test data not checked out")
@pytest.mark.parametrize("input_file,config", _private_test_data)
def test_regression_html_private(
    data_path: Path, input_file: str, config: dict[str, Any]
) -> None:
    """Regression test for private HTML data."""
    _run_html_regression_test(data_path, input_file, config)


def _run_html_regression_test(
    data_path: Path, input_file: str, config: dict[str, Any]
) -> None:
    file_path = data_path / input_file
    with open(
        str(file_path).replace(".html", "_abbreviations.json"), encoding="utf-8"
    ) as f:
        expected_abbreviations = json.load(f)
    with open(
        str(file_path).replace(".html", "_bioc.json"),
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)
    try:
        with open(
            str(file_path).replace(".html", "_tables.json"),
            encoding="utf-8",
        ) as f:
            expected_tables = json.load(f)
    except FileNotFoundError:
        expected_tables = {}

    auto_corpus = process_file(config=config, file_path=file_path)
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
    if auto_corpus.has_tables:
        assert tables == expected_tables
    else:
        assert not expected_tables


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
        str(expected_output_path).replace(".pdf", ".pdf_bioc.json"),
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)

    with open(
        str(expected_output_path).replace(".pdf", ".pdf_tables.json"),
        encoding="utf-8",
    ) as f:
        expected_tables = json.load(f)


    auto_corpus = process_file(config=config, file_path=pdf_path)

    new_bioc = auto_corpus.main_text
    new_tables = auto_corpus.tables

    _make_reproducible(new_bioc, expected_bioc, new_tables, expected_tables)

    assert new_bioc == expected_bioc
    assert new_tables == expected_tables


@pytest.mark.skip_ci_macos
@pytest.mark.skip_ci_windows
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
        d.pop("date", None)
        if docs := d.get("documents", []):
            for doc in docs:
                doc.pop("inputfile", None)
