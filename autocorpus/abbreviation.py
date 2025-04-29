"""Handles the processing of abbreviations.

modules used:
- collections: used for counting the most common occurrences
- datetime: datetime stamping
- pathlib: OS-agnostic pathing
- regex: regular expression matching/replacing
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

import regex as re2
from bs4 import BeautifulSoup, Tag

from . import logger


def _iter_sentences(text: str) -> Iterable[str]:
    """Iterate over sentences in text.

    The string is split at full stops and trailing whitespace is removed.
    """
    for sentence in text.split("."):
        yield sentence.strip()


def _remove_quotes(text: str) -> str:
    """Remove any quotes around potential candidate terms."""
    return re2.sub(r'([(])[\'"\p{Pi}]|[\'"\p{Pf}]([);:])', r"\1\2", text)


def _is_abbreviation(candidate: str) -> bool:
    r"""Check whether input string is an abbreviation.

    Based on Schwartz&Hearst.

    2 <= len(str) <= 10
    len(tokens) <= 2
    re.search(r'\p{L}', str)
    str[0].isalnum()

    and extra:
    if it matches (\p{L}\.?\s?){2,}
    it is a good candidate.

    Args:
        candidate: Candidate abbreviation

    Returns:
        True if this is a good candidate
    """
    viable = True

    # Broken: See https://github.com/omicsNLP/Auto-CORPus/issues/144
    # if re2.match(r"(\p{L}\.?\s?){2,}", candidate.lstrip()):
    #     viable = True
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


def _get_definition(candidate: str, preceding: str) -> str:
    """Return the definition for the given candidate.

    The definition is the set of tokens (in front of the candidate) that starts with
    a token starting with the first character of the candidate.
    """
    # Take the tokens in front of the candidate
    tokens = re2.split(r"[\s\-]+", preceding[:-1].lower())

    # the char that we are looking for
    key = candidate[0].lower()

    # Count the number of tokens that start with the same character as the candidate
    first_chars = [t[0] for t in filter(None, tokens)]

    definition_freq = first_chars.count(key)
    candidate_freq = candidate.lower().count(key)

    if candidate_freq > definition_freq:
        raise ValueError(
            "There are less keys in the tokens in front of candidate than there are in the candidate"
        )

    # Look for the list of tokens in front of candidate that
    # have a sufficient number of tokens starting with key
    # we should at least have a good number of starts
    count = 0
    start = 0
    start_index = len(first_chars) - 1
    while count < candidate_freq:
        if abs(start) > len(first_chars):
            raise ValueError(f"Candidate {candidate} not found")
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

    definition = preceding[start:].strip()

    # Extra sanity checks
    _validate_definition(candidate, definition)

    return definition


def _validate_definition(abbrev: str, definition: str) -> None:
    """Checks whether the chars in abbrev appear in the candidate definition.

    Based on:
        A simple algorithm for identifying abbreviation definitions in biomedical texts,
        Schwartz & Hearst

    Args:
        abbrev: Candidate abbreviation
        definition: Candidate definition
    """
    if len(definition) < len(abbrev):
        raise ValueError("Abbreviation is longer than definition")

    if abbrev in definition.split():
        raise ValueError("Abbreviation is full word of definition")

    s_index = -1
    l_index = -1

    while 1:
        long_char = definition[l_index].lower()
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
                        f"Definition for {abbrev} was not found in {definition}"
                    )

        else:
            if short_char == long_char:
                s_index -= 1
                l_index -= 1
            else:
                l_index -= 1

    definition = definition[l_index:]

    tokens = len(definition.split())
    length = len(abbrev)

    if tokens > min([length + 5, length * 2]):
        raise ValueError(
            f'Definition "{definition}" did not meet min(|A|+5, |A|*2) constraint'
        )

    # Do not return definitions that contain unbalanced parentheses
    if definition.count("(") != definition.count(")"):
        raise ValueError("Unbalanced parentheses not allowed in a definition")


def _get_best_candidates(sentence: str) -> Iterable[tuple[str, str] | None]:
    """Get the best candidate abbreviations in sentence with definitions.

    Args:
        sentence: Sentence which may contain candidate abbreviations and definitions

    Returns:
        An iterator of abbreviation/definition pairs or None for parsing errors
    """
    if "(" not in sentence:
        return

    # Check some things first
    if sentence.count("(") != sentence.count(")"):
        raise ValueError(f"Unbalanced parentheses: {sentence}")

    if sentence.find("(") > sentence.find(")"):
        raise ValueError(f"First parentheses is right: {sentence}")

    # Remove quotes around candidate definition
    sentence = _remove_quotes(sentence)

    close_index = -1
    while True:
        # Look for open parenthesis. Need leading whitespace to avoid matching
        # mathematical and chemical formulae
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

        if _is_abbreviation(candidate):
            try:
                definition = _get_definition(candidate, sentence[: start - 1])
            except (ValueError, IndexError) as e:
                logger.debug(f"Omitting candidate {candidate}. Reason: {e.args[0]}")
                yield None
            else:
                yield candidate, definition


def _extract_abbreviation_definition_pairs(
    doc_text: str,
) -> dict[str, str]:
    abbrev_map = defaultdict(list)
    omit = 0
    written = 0

    for i, sentence in enumerate(_iter_sentences(doc_text)):
        try:
            for candidate in _get_best_candidates(sentence):
                if not candidate:
                    # A parsing error occurred
                    omit += 1
                    continue

                # Append the current definition to the list of previous definitions
                abbrev, definition = candidate
                abbrev_map[abbrev].append(definition)
        except (ValueError, IndexError) as e:
            logger.debug(f"{i} Error processing sentence {sentence}: {e.args[0]}")
            omit += 1
    logger.debug(f"{written} abbreviations detected and kept ({omit} omitted)")

    # Return the most common definition for each term
    return {k: Counter(v).most_common(1)[0][0] for k, v in abbrev_map.items()}


def _list_to_dict(lst: list[str]) -> dict[str, str]:
    return {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}


def _abbre_table_to_dict(t: Tag) -> dict[str, str]:
    abbre_list = []
    rows = t.findAll("tr")
    for i in rows:
        elements = i.findAll(["td", "th"])
        vals = [j.get_text() for j in elements]
        if len(vals) > 1:
            abbre_list += vals

    return _list_to_dict(abbre_list)


def _abbre_list_to_dict(t: Tag) -> dict[str, str]:
    sf = t.findAll("dt")
    sf_list = [SF_word.get_text() for SF_word in sf]
    lf = t.findAll("dd")
    lf_list = [LF_word.get_text() for LF_word in lf]

    return dict(zip(sf_list, lf_list))


def _get_abbre_plain_text(t: Tag) -> list[str]:
    return t.get_text().split(";")


def _get_abbre_dict_given_by_author(soup: BeautifulSoup) -> dict[str, str]:
    header = soup.find_all("h2", recursive=True)
    for element in header:
        if not re2.search("abbreviation", element.get_text(), re2.IGNORECASE):
            continue

        nearest_down_tag = element.next_element
        while nearest_down_tag:
            tag_name = nearest_down_tag.name

            match tag_name:
                # when abbre is table
                case "table":
                    return _abbre_table_to_dict(nearest_down_tag)

                # when abbre is list
                case "dl":
                    return _abbre_list_to_dict(nearest_down_tag)

                # when abbre is plain text
                case "p":
                    abbre_list = _get_abbre_plain_text(nearest_down_tag)
                    if len(abbre_list) <= 2:
                        nearest_down_tag = nearest_down_tag.next_element
                        continue

                    abbre_dict = {}
                    for abbre_pair in abbre_list:
                        for sep in ":, ":
                            if abbre_pair.count(sep) == 1:
                                k, _, v = abbre_pair.partition(sep)
                                abbre_dict[k] = v
                                break
                    return abbre_dict

                # search until next h2
                case "h2":
                    break

                # move on to next tag
                case _:
                    nearest_down_tag = nearest_down_tag.next_element
    return {}


class Abbreviations:
    """Class for processing abbreviations using Auto-CORPus configurations."""

    def __get_abbreviations(self, main_text, soup, config):
        paragraphs = main_text["paragraphs"]
        all_abbreviations = {}
        for paragraph in paragraphs:
            all_abbreviations |= _extract_abbreviation_definition_pairs(
                paragraph["body"]
            )
        author_provided_abbreviations = _get_abbre_dict_given_by_author(soup)

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
