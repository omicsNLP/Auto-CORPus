"""Handles the processing of abbreviations.

modules used:
- logging: log errors/status messages
- collections: used for counting the most common occurrences
- datetime: datetime stamping
- pathlib: OS-agnostic pathing
- regex: regular expression matching/replacing
"""

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import regex as re2

from . import logger


class Abbreviations:
    """Class for processing abbreviations using Auto-CORPus configurations."""

    def __yield_lines_from_doc(self, doc_text):
        for line in doc_text.split("."):
            yield line.strip()

    def __conditions(self, candidate):
        r"""Based on Schwartz&Hearst.

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
        viable = True
        if re2.match(r"(\p{L}\.?\s?){2,}", candidate.lstrip()):
            viable = True
        if len(candidate) < 2 or len(candidate) > 10:
            viable = False
        if len(candidate.split()) > 2:
            viable = False
        if candidate.islower():  # customize function discard all lower case candidate
            viable = False
        if not re2.search(r"\p{L}", candidate):  # \p{L} = All Unicode letter
            viable = False
        if not candidate[0].isalnum():
            viable = False

        return viable

    def __best_candidates(self, sentence):
        """Locates the best candidates for an abbreviation.

        :param sentence: line read from input file
        :return: a Candidate iterator
        """
        if "(" in sentence:
            # Check some things first
            if sentence.count("(") != sentence.count(")"):
                raise ValueError(f"Unbalanced parentheses: {sentence}")

            if sentence.find("(") > sentence.find(")"):
                raise ValueError(f"First parentheses is right: {sentence}")

            close_index = -1
            while 1:
                # Look for open parenthesis. Need leading whitespace to avoid matching mathematical and chemical formulae
                open_index = sentence.find(" (", close_index + 1)

                if open_index == -1:
                    break

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
                    if char == "(":
                        open_count += 1
                    elif char in [")", ";", ":"]:
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

                if self.__conditions(candidate):
                    new_candidate = Candidate(candidate)
                    new_candidate.set_position(start, stop)
                    yield new_candidate

    def __get_definition(self, candidate, sentence):
        """Takes a candidate and a sentence and returns the definition candidate.The definition candidate is the set of tokens (in front of the candidate) that starts with a token starting with the first character of the candidate.

        :param candidate: candidate abbreviation
        :param sentence: current sentence (single line from input file)
        :return: candidate definition for this abbreviation
        """
        # Take the tokens in front of the candidate
        tokens = re2.split(r"[\s\-]+", sentence[: candidate.start - 2].lower())

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
                    raise ValueError(f"candidate {candidate} not found")
                start -= 1
                # Look up key in the definition
                try:
                    start_index = first_chars.index(key, len(first_chars) + start)
                except ValueError:
                    pass

                # Count the number of keys in definition
                count = first_chars[start_index:].count(key)

            # We found enough keys in the definition so return the definition as a definition candidate
            start = len(" ".join(tokens[:start_index]))
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
            raise ValueError(
                "There are less keys in the tokens in front of candidate than there are in the candidate"
            )

    def __select_definition(self, definition, abbrev):
        """Takes a definition candidate and an abbreviation candidate and returns True if the chars in the abbreviation occur in the definition.

        Based on
        A simple algorithm for identifying abbreviation definitions in biomedical texts, Schwartz & Hearst
        :param definition: candidate definition
        :param abbrev: candidate abbreviation
        :return:
        """
        if len(definition) < len(abbrev):
            raise ValueError("Abbreviation is longer than definition")

        if abbrev in definition.split():
            raise ValueError("Abbreviation is full word of definition")

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
                    if (
                        l_index == -1 * len(definition)
                        or not definition[l_index - 1].isalnum()
                    ):
                        break
                    else:
                        l_index -= 1
                else:
                    l_index -= 1
                    if l_index == -1 * (len(definition) + 1):
                        raise ValueError(
                            f"definition {abbrev} was not found in {definition}"
                        )

            else:
                if short_char == long_char:
                    s_index -= 1
                    l_index -= 1
                else:
                    l_index -= 1

        new_candidate = Candidate(definition[l_index : len(definition)])
        new_candidate.set_position(definition.start, definition.stop)
        definition = new_candidate

        tokens = len(definition.split())
        length = len(abbrev)

        if tokens > min([length + 5, length * 2]):
            raise ValueError("did not meet min(|A|+5, |A|*2) constraint")

        # Do not return definitions that contain unbalanced parentheses
        if definition.count("(") != definition.count(")"):
            raise ValueError("Unbalanced parentheses not allowed in a definition")

        return definition

    def __extract_abbreviation_definition_pairs(
        self,
        doc_text=None,
        most_common_definition=False,
        first_definition=False,
        all_definition=True,
    ):
        abbrev_map = dict()
        list_abbrev_map = defaultdict(list)
        counter_abbrev_map = dict()
        omit = 0
        written = 0
        sentence_iterator = enumerate(self.__yield_lines_from_doc(doc_text))

        collect_definitions = False
        if most_common_definition or first_definition or all_definition:
            collect_definitions = True

        for i, sentence in sentence_iterator:
            # Remove any quotes around potential candidate terms
            clean_sentence = re2.sub(
                r'([(])[\'"\p{Pi}]|[\'"\p{Pf}]([);:])', r"\1\2", sentence
            )
            try:
                for candidate in self.__best_candidates(clean_sentence):
                    try:
                        definition = self.__get_definition(candidate, clean_sentence)
                    except (ValueError, IndexError) as e:
                        logger.debug(
                            f"{i} Omitting candidate {candidate}. Reason: {e.args[0]}"
                        )
                        omit += 1
                    else:
                        try:
                            definition = self.__select_definition(definition, candidate)
                        except (ValueError, IndexError) as e:
                            logger.debug(
                                f"{i} Omitting definition {definition} for candidate {candidate}. Reason: {e.args[0]}"
                            )
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
                logger.debug(f"{i} Error processing sentence {sentence}: {e.args[0]}")
        logger.debug(f"{written} abbreviations detected and kept ({omit} omitted)")

        # Return most common definition for each term
        if collect_definitions:
            if most_common_definition:
                # Return the most common definition for each term
                for k, v in list_abbrev_map.items():
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
        pairs = self.__extract_abbreviation_definition_pairs(
            doc_text=main_text, most_common_definition=True
        )

        return pairs

    def __list_to_dict(self, lst):
        op = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
        return op

    def __abbre_table_to_dict(self, t):
        abbre_list = []
        rows = t.findAll("tr")
        for i in rows:
            elements = i.findAll(["td", "th"])
            vals = [j.get_text() for j in elements]
            if len(vals) > 1:
                abbre_list += vals
        abbre_dict = self.__list_to_dict(abbre_list)
        return abbre_dict

    def __abbre_list_to_dict(self, t):
        sf = t.findAll("dt")
        sf_list = [SF_word.get_text() for SF_word in sf]
        lf = t.findAll("dd")
        lf_list = [LF_word.get_text() for LF_word in lf]
        abbre_dict = dict(zip(sf_list, lf_list))
        return abbre_dict

    def __get_abbre_plain_text(self, soup_og):
        abbre_text = soup_og.get_text()
        abbre_list = abbre_text.split(";")
        list_lenth = len(abbre_list)
        return abbre_list, list_lenth

    def __get_abbre_dict_given_by_author(self, soup_og):
        header = soup_og.find_all("h2", recursive=True)
        abbre_dict = {}
        for element in header:
            if re2.search("abbreviation", element.get_text(), re2.IGNORECASE):
                nearest_down_tag = element.next_element
                while nearest_down_tag:
                    tag_name = nearest_down_tag.name

                    # when abbre is table
                    if tag_name == "table":
                        abbre_dict = self.__abbre_table_to_dict(nearest_down_tag)
                        break

                    # when abbre is list
                    elif tag_name == "dl":
                        abbre_dict = self.__abbre_list_to_dict(nearest_down_tag)
                        break

                    # when abbre is plain text
                    elif tag_name == "p":
                        abbre_list, list_lenth = self.__get_abbre_plain_text(
                            nearest_down_tag
                        )
                        if list_lenth <= 2:
                            nearest_down_tag = nearest_down_tag.next_element
                            continue
                        else:
                            for abbre_pair in abbre_list:
                                if len(abbre_pair.split(":")) == 2:
                                    abbre_dict.update(
                                        {
                                            abbre_pair.split(":")[0]: abbre_pair.split(
                                                ":"
                                            )[1]
                                        }
                                    )
                                elif len(abbre_pair.split(",")) == 2:
                                    abbre_dict.update(
                                        {
                                            abbre_pair.split(",")[0]: abbre_pair.split(
                                                ","
                                            )[1]
                                        }
                                    )
                                elif len(abbre_pair.split(" ")) == 2:
                                    abbre_dict.update(
                                        {
                                            abbre_pair.split(" ")[0]: abbre_pair.split(
                                                " "
                                            )[1]
                                        }
                                    )
                            break

                    # search until next h2
                    elif tag_name == "h2":
                        break
                    else:
                        nearest_down_tag = nearest_down_tag.next_element
        return abbre_dict

    def __get_abbreviations(self, main_text, soup, config):
        paragraphs = main_text["paragraphs"]
        all_abbreviations = {}
        for paragraph in paragraphs:
            maintext = paragraph["body"]
            pairs = self.__extract_abbreviation(maintext)
            all_abbreviations.update(pairs)
        author_provided_abbreviations = self.__get_abbre_dict_given_by_author(soup)

        abbrev_json = {}

        for key in author_provided_abbreviations.keys():
            abbrev_json[key] = {
                author_provided_abbreviations[key]: ["abbreviations section"]
            }
        for key in all_abbreviations:
            if key in abbrev_json:
                if all_abbreviations[key] in abbrev_json[key].keys():
                    abbrev_json[key][all_abbreviations[key]].append("fulltext")
                else:
                    abbrev_json[key][all_abbreviations[key]] = ["fulltext"]
            else:
                abbrev_json[key] = {all_abbreviations[key]: ["fulltext"]}

        return abbrev_json

    def __biocify_abbreviations(self, abbreviations, file_path):
        template = {
            "source": "Auto-CORPus (abbreviations)",
            "date": f"{datetime.today().strftime('%Y%m%d')}",
            "key": "autocorpus_abbreviations.key",
            "documents": [
                {
                    "id": Path(file_path).name.split(".")[0],
                    "inputfile": file_path,
                    "passages": [],
                }
            ],
        }
        passages = template["documents"][0]["passages"]
        for short in abbreviations.keys():
            counter = 1
            short_template = {"text_short": short}
            for long in abbreviations[short].keys():
                short_template[f"text_long_{counter}"] = long.replace("\n", " ")
                short_template[f"extraction_algorithm_{counter}"] = ", ".join(
                    abbreviations[short][long]
                )
                counter += 1
            passages.append(short_template)
        return template

    def __init__(self, main_text, soup, config, file_path):
        """Extract abbreviations from the input main text, using the provided soup and config objects.

        Args:
            main_text (str): Article main text data
            soup (bs4.BeautifulSoup): Article as a BeautifulSoup object
            config (dict): AC configuration rules
            file_path (str): Input file path
        """
        self.abbreviations = self.__biocify_abbreviations(
            self.__get_abbreviations(main_text, soup, config), file_path
        )

    def to_dict(self):
        """Retrieves abbreviations BioC dict.

        Returns (dict): abbreviations BioC dict.
        """
        return self.abbreviations


class Candidate(str):
    """Candidate string."""

    def __init__(self, value):
        """Stores the start/stop positions within strings.

        Args:
            value (str): Candidate value
        """
        super().__init__()
        self.start = 0
        self.stop = 0

    def set_position(self, start, stop):
        """Setter for the start and stop positions within a candidate instance.

        Args:
            start (int): start index of the candidate.
            stop (int): stop index of the candidate.
        """
        self.start = start
        self.stop = stop
