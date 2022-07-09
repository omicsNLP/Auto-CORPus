import json
from datetime import datetime

from src.bioc_documents import BiocDocument


class BiocFormatter:

    @staticmethod
    def build_bioc_format(input_vals):
        return {
            "source": "Auto-CORPus (full-text)",
            "date": f'{datetime.today().strftime("%Y%m%d")}',
            "key": "autocorpus_fulltext.key",
            "infons": {},
            "documents": [BiocDocument(input_vals).as_dict()]
        }

    def __init__(self, input_vals):
        self.bioc_output = self.build_bioc_format(input_vals)

    def to_json(self, indent_val=None):
        return json.dumps(self.bioc_output, indent=indent_val, ensure_ascii=False)

    def to_dict(self):
        return self.bioc_output
