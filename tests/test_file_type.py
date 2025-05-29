"""Test the file_type checking utilities."""

from pathlib import Path

from lxml import etree


def test_check_file_type_html(tmp_path: Path, data_path: Path) -> None:
    """Test that HTML files are correctly identified."""
    from autocorpus.file_type import FileType, check_file_type

    html_file = data_path / "PMC" / "Current" / "PMC8885717.html"
    assert check_file_type(html_file) == FileType.HTML

    json_file = data_path / "PMC" / "Current" / "PMC8885717_bioc.json"
    assert check_file_type(json_file) == FileType.OTHER

    pdf_file = data_path / "Supplementary" / "PDF" / "tp-10-08-2123-coif.pdf"
    assert check_file_type(pdf_file) == FileType.PDF

    # Create temporary XML file
    xml_file = tmp_path / "output.xml"
    with xml_file.open("wb") as out:
        out.write(etree.tostring(etree.XML("<root>data</root>"), xml_declaration=True))

    assert check_file_type(xml_file) == FileType.XML
