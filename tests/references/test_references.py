"""Test the references section of the PMC example."""

import pytest
from bs4 import BeautifulSoup
from reference_data import example_pmc_correct_reference, example_pmc_reference


@pytest.mark.parametrize(
    "input_ref_html, correct_references",
    [
        (
            example_pmc_reference,
            example_pmc_correct_reference,
        ),
    ],
)
def test_references(input_ref_html: str, correct_references: dict[str, str]) -> None:
    """A regression test for the references section of the PMC example."""
    from autocorpus.references import get_reference

    soup = BeautifulSoup(input_ref_html, "html.parser")
    refs = get_reference({"node": soup}, "References")

    assert refs == correct_references
