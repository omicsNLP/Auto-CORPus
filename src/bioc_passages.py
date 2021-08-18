import json


class BioCPassage:

	@classmethod
	def from_title(cls, title, offset):
		title_passage = {
			"section_heading": "",
			"subsection_heading": "",
			"body": title,
			"IAO_term": ["document title"],
			"IAO_ID": ["IAO:0000305"]
		}
		return cls(title_passage, offset)

	def __build_passage(self, passage, offset):
		passage_dict= {
			"offset": offset,
			"infons": {
				"section_type": [{"IAO_name": n,"IAO_id": i} for n, i in zip(passage['IAO_term'], passage['IAO_ID'])]
			},
			"text": passage['body'],
			"sentences": [],
			"annotations": [],
			"relations": []
		}
		# TODO: currently assumes section_heading and subsection_heading will always exist, should ideally check for existence.
		#  Also doesn't account for subsubsection headings which might exist
		if passage['section_heading'] != "":
			passage_dict['infons']['section_title_1'] = passage['section_heading']
		if passage['subsection_heading'] != "":
			passage_dict['infons']['section_title_2'] = passage["subsection_heading"]

		return passage_dict

	def __init__(self, passage, offset):
		self.offset = 0
		self.passage = self.__build_passage(passage, offset)
		pass

	def as_dict(self):
		return self.passage