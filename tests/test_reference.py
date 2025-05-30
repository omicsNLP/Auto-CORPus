"""Test the references section of the PMC example."""

from unittest.mock import MagicMock


def test_references() -> None:
    """A regression test for the references section of the PMC example."""
    from autocorpus.reference import ReferencesParagraph, get_references

    node = MagicMock()
    node.get_text.return_value = "NODE  TEXT\n"
    ref = {"node": node, "title": ["A"], "journal": ["B", "C"], "volume": ["1"]}
    expected = ReferencesParagraph(
        section_heading="References",
        subsection_heading="",
        body="NODE TEXT",
        section_type=[{"iao_name": "references section", "iao_id": "IAO:0000320"}],
        title="A",
        journal="B. C",
        volume="1",
    )

    assert expected == get_references(ref, "References")


def test_references_paragraph_as_dict() -> None:
    """Test the ReferencesParagraph dataclass."""
    from autocorpus.reference import ReferencesParagraph

    ref = ReferencesParagraph(
        section_heading="References",
        subsection_heading="",
        body="NODE TEXT",
        section_type=[{"iao_name": "references section", "iao_id": "IAO:0000320"}],
        title="A",
        journal="B. C",
        volume="1",
    )

    assert ref.as_dict() == {
        "section_heading": "References",
        "subsection_heading": "",
        "body": "NODE TEXT",
        "section_type": [{"iao_name": "references section", "iao_id": "IAO:0000320"}],
        "title": "A",
        "journal": "B. C",
        "volume": "1",
    }

    ref = ReferencesParagraph(
        section_heading="References",
        subsection_heading="",
        body="NODE TEXT",
        section_type=[{"iao_name": "references section", "iao_id": "IAO:0000320"}],
        title="A",
    )

    assert ref.as_dict() == {
        "section_heading": "References",
        "subsection_heading": "",
        "body": "NODE TEXT",
        "section_type": [{"iao_name": "references section", "iao_id": "IAO:0000320"}],
        "title": "A",
    }
