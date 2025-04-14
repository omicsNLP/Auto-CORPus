"""Top-level BioC collection builder script."""

import json
from datetime import datetime

from .bioc_documents import get_formatted_bioc_document


class BiocFormatter:
    """BioC Collection builder/formatter."""

    def build_bioc_format(self, input_vals):
        """Constructs a BioC collection from input document-level data.

        Args:
            input_vals (object): Input document-level data.

        Returns:
            (dict): BioC collection
        """
        return {
            "source": "Auto-CORPus (full-text)",
            "date": f"{datetime.today().strftime('%Y%m%d')}",
            "key": "autocorpus_fulltext.key",
            "infons": {},
            "documents": [get_formatted_bioc_document(input_vals)],
        }

    def __init__(self, input_vals):
        """Top-level BioC formatter utility.

        Args:
            input_vals (object): Input document-level data.
        """
        self.bioc_output = self.build_bioc_format(input_vals)

    def to_json(self, indent_val=None):
        """Returns a JSON representation of the BioC collection.

        Args:
            indent_val (int): level of indentation for the JSON output

        Returns:
            (str): JSON representation of the BioC collection
        """
        return json.dumps(self.bioc_output, indent=indent_val, ensure_ascii=False)

    def to_dict(self):
        """Returns a dictionary representation of the BioC collection.

        Returns:
            (dict): dictionary representation of the BioC collection
        """
        return self.bioc_output
