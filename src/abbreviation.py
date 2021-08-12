import logging
import regex as re2
from collections import defaultdict, Counter
from src.utils import *



class abbreviations:

	def __yield_lines_from_doc(self, doc_text):
		for line in doc_text.split("."):
			yield line.strip()

	def __conditions(self, candidate):
		"""
		Based on Schwartz&Hearst

		2 <= len(str) <= 10
		len(tokens) <= 2
		re.search(r'\p{L}', str)
		str[0].isalnum()

		and extra:
		if it matches (\p{L}\.?\s?){2,}
		it is a good candidate.

		:param candidate: candidate abbreviation
		:return: True if this is a good candidate
		"""
		LF_in_parentheses=False
		viable = True
		if re2.match(r'(\p{L}\.?\s?){2,}', candidate.lstrip()):
			viable = True
		if len(candidate) < 2 or len(candidate) > 10:
			viable = False
		if len(candidate.split()) > 2:
			viable = False
			LF_in_parentheses=True                #customize funcition find LF in parentheses
		if candidate.islower():                   #customize funcition discard all lower case candidate
			viable = False
		if not re2.search(r'\p{L}', candidate): # \p{L} = All Unicode letter
			viable = False
		if not candidate[0].isalnum():
			viable = False

		return viable

	def __best_candidates(self, sentence):
		"""
		:param sentence: line read from input file
		:return: a Candidate iterator
		"""

		if '(' in sentence:
			# Check some things first
			if sentence.count('(') != sentence.count(')'):
				raise ValueError("Unbalanced parentheses: {}".format(sentence))

			if sentence.find('(') > sentence.find(')'):
				raise ValueError("First parentheses is right: {}".format(sentence))

			close_index = -1
			while 1:
				# Look for open parenthesis. Need leading whitespace to avoid matching mathematical and chemical formulae
				open_index = sentence.find(' (', close_index + 1)

				if open_index == -1: break

				# Advance beyond whitespace
				open_index += 1

				# Look for closing parentheses
				close_index = open_index + 1
				open_count = 1
				skip = False
				while open_count:
					try:
						char = sentence[close_index]
					except IndexError:
						# We found an opening bracket but no associated closing bracket
						# Skip the opening bracket
						skip = True
						break
					if char == '(':
						open_count += 1
					elif char in [')', ';', ':']:
						open_count -= 1
					close_index += 1

				if skip:
					close_index = open_index + 1
					continue

				# Output if conditions are met
				start = open_index + 1
				stop = close_index - 1
				candidate = sentence[start:stop]

				# Take into account whitespace that should be removed
				start = start + len(candidate) - len(candidate.lstrip())
				stop = stop - len(candidate) + len(candidate.rstrip())
				candidate = sentence[start:stop]
				#print (candidate)

				if self.__conditions(candidate):
					new_candidate = Candidate(candidate)
					new_candidate.set_position(start, stop)
					yield new_candidate
			#elif LF_in_parentheses:

	def __get_definition(self, candidate, sentence):
		"""
		Takes a candidate and a sentence and returns the definition candidate.

		The definition candidate is the set of tokens (in front of the candidate)
		that starts with a token starting with the first character of the candidate

		:param candidate: candidate abbreviation
		:param sentence: current sentence (single line from input file)
		:return: candidate definition for this abbreviation
		"""
		# Take the tokens in front of the candidate
		tokens = re2.split(r'[\s\-]+', sentence[:candidate.start - 2].lower())
		# the char that we are looking for
		key = candidate[0].lower()

		# Count the number of tokens that start with the same character as the candidate
		first_chars = [t[0] for t in filter(None, tokens)]

		definition_freq = first_chars.count(key)
		candidate_freq = candidate.lower().count(key)

		# Look for the list of tokens in front of candidate that
		# have a sufficient number of tokens starting with key
		if candidate_freq <= definition_freq:
			# we should at least have a good number of starts
			count = 0
			start = 0
			start_index = len(first_chars) - 1
			while count < candidate_freq:
				if abs(start) > len(first_chars):
					raise ValueError("candidate {} not found".format(candidate))
				start -= 1
				# Look up key in the definition
				try:
					start_index = first_chars.index(key, len(first_chars) + start)
				except ValueError:
					pass

				# Count the number of keys in definition
				count = first_chars[start_index:].count(key)

			# We found enough keys in the definition so return the definition as a definition candidate
			start = len(' '.join(tokens[:start_index]))
			stop = candidate.start - 1
			candidate = sentence[start:stop]

			# Remove whitespace
			start = start + len(candidate) - len(candidate.lstrip())
			stop = stop - len(candidate) + len(candidate.rstrip())
			candidate = sentence[start:stop]

			new_candidate = Candidate(candidate)
			new_candidate.set_position(start, stop)
			return new_candidate

		else:
			raise ValueError('There are less keys in the tokens in front of candidate than there are in the candidate')


	def __select_definition(self, definition, abbrev):
		"""
		Takes a definition candidate and an abbreviation candidate
		and returns True if the chars in the abbreviation occur in the definition

		Based on
		A simple algorithm for identifying abbreviation definitions in biomedical texts, Schwartz & Hearst
		:param definition: candidate definition
		:param abbrev: candidate abbreviation
		:return:
		"""

		if len(definition) < len(abbrev):
			raise ValueError('Abbreviation is longer than definition')

		if abbrev in definition.split():
			raise ValueError('Abbreviation is full word of definition')

		s_index = -1
		l_index = -1

		while 1:
			try:
				long_char = definition[l_index].lower()
			except IndexError:
				raise

			short_char = abbrev[s_index].lower()

			if not short_char.isalnum():
				s_index -= 1

			if s_index == -1 * len(abbrev):
				if short_char == long_char:
					if l_index == -1 * len(definition) or not definition[l_index - 1].isalnum():
						break
					else:
						l_index -= 1
				else:
					l_index -= 1
					if l_index == -1 * (len(definition) + 1):
						raise ValueError("definition {} was not found in {}".format(abbrev, definition))

			else:
				if short_char == long_char:
					s_index -= 1
					l_index -= 1
				else:
					l_index -= 1

		new_candidate = Candidate(definition[l_index:len(definition)])
		new_candidate.set_position(definition.start, definition.stop)
		definition = new_candidate

		tokens = len(definition.split())
		length = len(abbrev)

		if tokens > min([length + 5, length * 2]):
			raise ValueError("did not meet min(|A|+5, |A|*2) constraint")

		# Do not return definitions that contain unbalanced parentheses
		if definition.count('(') != definition.count(')'):
			raise ValueError("Unbalanced parentheses not allowed in a definition")

		return definition




	def __extract_abbreviation_definition_pairs(self, file_path=None,
	                                            doc_text=None,
	                                            most_common_definition=False,
	                                            first_definition=False,
	                                            all_definition=True):
		abbrev_map = dict()
		list_abbrev_map = defaultdict(list)
		counter_abbrev_map = dict()
		omit = 0
		written = 0
		if file_path:
			sentence_iterator = enumerate(yield_lines_from_file(file_path))
		elif doc_text:
			sentence_iterator = enumerate(self.__yield_lines_from_doc(doc_text))
		else:
			return abbrev_map

		collect_definitions = False
		if most_common_definition or first_definition or all_definition:
			collect_definitions = True

		for i, sentence in sentence_iterator:
			# Remove any quotes around potential candidate terms
			clean_sentence = re2.sub(r'([(])[\'"\p{Pi}]|[\'"\p{Pf}]([);:])', r'\1\2', sentence)
			try:
				for candidate in self.__best_candidates(clean_sentence):
					try:
						definition = self.__get_definition(candidate, clean_sentence)
					except (ValueError, IndexError) as e:
						self.log.debug("{} Omitting candidate {}. Reason: {}".format(i, candidate, e.args[0]))
						omit += 1
					else:
						try:
							definition = self.__select_definition(definition, candidate)
						except (ValueError, IndexError) as e:
							self.log.debug("{} Omitting definition {} for candidate {}. Reason: {}".format(i, definition, candidate, e.args[0]))
							omit += 1
						else:
							# Either append the current definition to the list of previous definitions ...
							if collect_definitions:
								list_abbrev_map[candidate].append(definition)
							else:
								# Or update the abbreviations map with the current definition
								abbrev_map[candidate] = definition
							written += 1
			except (ValueError, IndexError) as e:
				self.log.debug("{} Error processing sentence {}: {}".format(i, sentence, e.args[0]))
		self.log.debug("{} abbreviations detected and kept ({} omitted)".format(written, omit))

		# Return most common definition for each term
		if collect_definitions:
			if most_common_definition:
				# Return the most common definition for each term
				for k,v in list_abbrev_map.items():
					counter_abbrev_map[k] = Counter(v).most_common(1)[0][0]
			elif first_definition:
				# Return the first definition for each term
				for k, v in list_abbrev_map.items():
					counter_abbrev_map[k] = v
			elif all_definition:
				for k, v in list_abbrev_map.items():
					counter_abbrev_map[k] = v
			return counter_abbrev_map

		# Or return the last encountered definition for each term
		return abbrev_map


	def __extract_abbreviation(self, main_text):
		text_to_be_written=''
		pairs = self.__extract_abbreviation_definition_pairs(doc_text=main_text,most_common_definition=True)

		return pairs


	def __get_abbreviations(self, main_text, soup, config):
		paragraphs = main_text['paragraphs']
		all_abbreviations = {}
		for paragraph in paragraphs:
			maintext = paragraph['body']
			pairs = self.__extract_abbreviation(maintext)
			all_abbreviations.update(pairs)


		abbreviations_table = soup.find(
			config['abbreviations_table']['name'], config['abbreviations_table']['attrs'])
		abbreviations = {}
		for tr in abbreviations_table.find_all('tr'):
			short_form, long_form = [td.get_text() for td in tr.find_all('td')]
			abbreviations[short_form] = long_form

		author_provided_abbreviations = abbreviations
		additional_abbreviations = {}
		lc_author_keys = [x.lower() for x in author_provided_abbreviations.keys()]
		for key in all_abbreviations.keys():
			if key.lower() not in lc_author_keys:
				additional_abbreviations[key] = all_abbreviations[key]

		all_abbreviations.update(author_provided_abbreviations)

		abbrev_json = {}
		abbrev_json['author_provided_abbreviations'] = author_provided_abbreviations
		abbrev_json['additional_abbreviations'] = additional_abbreviations
		abbrev_json['all_abbreviations'] = all_abbreviations
		return abbrev_json

	def __init__(self, main_text, soup, config):
		logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
		self.log = logging.getLogger(__name__)

		self.abbreviations = self.__get_abbreviations(main_text, soup, config)
		pass

	def to_dict(self):
		return self.abbreviations


class Candidate(str):
	def __init__(self, value):
		super().__init__()
		self.start = 0
		self.stop = 0

	def set_position(self, start, stop):
		self.start = start
		self.stop = stop