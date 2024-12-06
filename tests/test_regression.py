import json
from pathlib import Path


def test_autoCORPus():
    """A regression test for the main autoCORPus class on the AutoCORPus Paper.

    The test data output is built using `run_app.py` with the following arguments:
    ```
    python run_app.py -c "configs/config_pmc.json" -t "tests/data" -f tests/data/PMC8885717.html -o JSON
    ```
    """
    from autocorpus.autoCORPus import autoCORPus

    with open(
        Path(__file__).parent
        / "data"
        / "PMC"
        / "Pre-Oct-2024"
        / "PMC8885717_abbreviations.json",
        encoding="utf-8",
    ) as f:
        expected_abbreviations = json.load(f)
    with open(
        Path(__file__).parent
        / "data"
        / "PMC"
        / "Pre-Oct-2024"
        / "PMC8885717_bioc.json",
        encoding="utf-8",
    ) as f:
        expected_bioc = json.load(f)
    with open(
        Path(__file__).parent
        / "data"
        / "PMC"
        / "Pre-Oct-2024"
        / "PMC8885717_tables.json",
        encoding="utf-8",
    ) as f:
        expected_tables = json.load(f)

    auto_corpus = autoCORPus(
        "autocorpus/configs/config_pmc_pre_oct_2024.json",
        base_dir="tests/data/PMC/Pre-Oct-2024",
        main_text="tests/data/PMC/Pre-Oct-2024/PMC8885717.html",
    )

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
