"""Module to run the autocorpus pipeline."""

from pathlib import Path

from .file_processing import process_file


def run_autocorpus(config, structure, key, output_format):
    """Run the autocorpus pipeline on a given file.

    Args:
        config: The configuration file to use.
        structure: The structure of the input files.
        key: The key in the structure dict for the current file.
        output_format: The output format to use (JSON or XML).
    """
    ac = process_file(
        config=config,
        file_path=Path(structure[key]["main_text"]),
        linked_tables=sorted(Path(lt) for lt in structure[key]["linked_tables"]),
    )

    out_dir = Path(structure[key]["out_dir"])
    if structure[key]["main_text"]:
        key = key.replace("\\", "/")
        if output_format.lower() == "json":
            with open(
                out_dir / f"{Path(key).name}_bioc.json",
                "w",
                encoding="utf-8",
            ) as outfp:
                outfp.write(ac.main_text_to_bioc_json())
        else:
            with open(
                out_dir / f"{Path(key).name}_bioc.xml",
                "w",
                encoding="utf-8",
            ) as outfp:
                outfp.write(ac.main_text_to_bioc_xml())
        with open(
            out_dir / f"{Path(key).name}_abbreviations.json",
            "w",
            encoding="utf-8",
        ) as outfp:
            outfp.write(ac.abbreviations_to_bioc_json())

        ## TODO: Uncomment when SI conversion is supported
        # out_filename = str(file_path).replace(".pdf", ".pdf_bioc.json")
        # with open(out_filename, "w", encoding="utf-8") as f:
        #     BioCJSON.dump(bioc_text, f, indent=4)

        # out_table_filename = str(file_path).replace(".pdf", ".pdf_tables.json")
        # with open(out_table_filename, "w", encoding="utf-8") as f:
        #     BioCTableJSON.dump(bioc_tables, f, indent=4)

    # AC does not support the conversion of tables or abbreviations to XML
    if ac.has_tables:
        with open(
            out_dir / f"{Path(key).name}_tables.json", "w", encoding="utf-8"
        ) as outfp:
            outfp.write(ac.tables_to_bioc_json())
