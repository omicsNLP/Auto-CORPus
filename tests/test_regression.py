import json
from pathlib import Path


def test_autoCORPus():
    """A regression test for the main autoCORPus class on the AutoCORPus Paper.

    The test data output is built using `run_app.py` with the following arguments:
    ```
    python run_app.py -c "configs/config_pmc.json" -t "tests/data" -f tests/data/PMC8885717.html -o JSON
    ```
    """
    from src.autoCORPus import autoCORPus

    with open(Path(__file__).parent / "data" / "PMC8885717_abbreviations.json") as f:
        expected_abbreviations = json.load(f)
    with open(Path(__file__).parent / "data" / "PMC8885717_bioc.json") as f:
        expected_bioc = json.load(f)
    with open(Path(__file__).parent / "data" / "PMC8885717_tables.json") as f:
        expected_tables = json.load(f)

    auto_corpus = autoCORPus(
        "configs/config_pmc.json",
        base_dir="tests/data",
        main_text="tests/data/PMC8885717.html",
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
