"""Test the references section of the PMC example."""

from unittest.mock import MagicMock


def test_references() -> None:
    """A regression test for the references section of the PMC example."""
    from autocorpus.references import get_reference

    node = MagicMock()
    node.get_text.return_value = "NODE  TEXT\n"
    ref = {"node": node, "a": ["A"], "b": ["B", "C"]}
    expected = {
        "section_heading": "References",
        "subsection_heading": "",
        "body": "NODE TEXT",
        "section_type": [{"iao_name": "references section", "iao_id": "IAO:0000320"}],
        "a": "A",
        "b": "B. C",
    }

    assert expected == get_reference(ref, "References")
