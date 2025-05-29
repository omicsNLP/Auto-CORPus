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
from typing import Any

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


def _is_abbreviation(s: str) -> bool:
    """Check whether input string is an abbreviation.

    To be classified as an abbreviation, a string must be composed exclusively of
    Unicode letters or digits, optionally separated by dots or hyphens. This sequence
    must repeat between two and ten times. We exclude strings that are *exclusively*
    composed of digits or lowercase letters.

    Adapted from Schwartz & Hearst.
    """
    # Disallow if exclusively composed of digits
    if re2.match(r"\p{N}+$", s):
        return False

    # Disallow if exclusively composed of lowercase unicode chars
    if re2.match(r"\p{Ll}+$", s):
        return False

    # Should be a repeating sequence of unicode chars or digits, optionally separated
    # by dots or hyphens. The sequence must repeat between 2 and 10 times.
    return bool(re2.match(r"([\p{L}\p{N}][\.\-]?){2,10}$", s))


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


_AbbreviationsDict = dict[str, dict[str, list[str]]]


def _extract_abbreviations(
    main_text: dict[str, Any], soup: BeautifulSoup
) -> _AbbreviationsDict:
    paragraphs = main_text["paragraphs"]
    all_abbreviations: dict[str, str] = {}
    for paragraph in paragraphs:
        all_abbreviations |= _extract_abbreviation_definition_pairs(paragraph["body"])
    author_provided_abbreviations = _get_abbre_dict_given_by_author(soup)

    abbrev_json: _AbbreviationsDict = {}

    for k, v in author_provided_abbreviations.items():
        abbrev_json[k] = {v: ["abbreviations section"]}

    for k, v in all_abbreviations.items():
        if k not in abbrev_json:
            abbrev_json[k] = {}
        if v not in abbrev_json[k]:
            abbrev_json[k][v] = []

        abbrev_json[k][v].append("fulltext")

    return abbrev_json


def _biocify_abbreviations(
    abbreviations: _AbbreviationsDict, file_path: Path
) -> dict[str, Any]:
    passages = []
    for short, long in abbreviations.items():
        counter = 1
        short_template = {"text_short": short}
        for definition, kinds in long.items():
            short_template[f"text_long_{counter}"] = definition.replace("\n", " ")
            short_template[f"extraction_algorithm_{counter}"] = ", ".join(kinds)
            counter += 1
        passages.append(short_template)

    return {
        "source": "Auto-CORPus (abbreviations)",
        "date": datetime.today().strftime("%Y%m%d"),
        "key": "autocorpus_abbreviations.key",
        "documents": [
            {
                "id": file_path.name.partition(".")[0],
                "inputfile": str(file_path),
                "passages": passages,
            }
        ],
    }


def get_abbreviations(
    main_text: dict[str, Any], soup: BeautifulSoup, file_path: Path
) -> dict[str, Any]:
    """Extract abbreviations from the input main text.

    Args:
        main_text: Article main text data
        soup: Article as a BeautifulSoup object
        file_path: Input file path

    Returns:
        Abbreviations in BioC format.
    """
    return _biocify_abbreviations(_extract_abbreviations(main_text, soup), file_path)
