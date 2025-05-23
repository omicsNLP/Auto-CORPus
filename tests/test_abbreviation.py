"""Tests for the abbreviation module."""

from itertools import chain, repeat

import pytest

from autocorpus.abbreviation import _is_abbreviation

_ABBREVIATIONS = (
    "ABC",
    "H.P.",  # can be separated by dots
    "A.BC",  # we don't enforce that there is a dot after every letter
    "HOUSE",  # allowed: all caps
    "House",  # allowed: at least one letter is capital (odd though)
    "ÄBÇ",  # we support unicode chars
    "3ABC",  # we allow numbers
    "ABC3",
    "A.B.3.",  # abbreviations with numbers can still be separated by dots
    "a.b.c.",  # all lowercase strings are fine if separated by dots
    "A.B." * 5,  # long string, but separated by dots, so also fine
)
_NON_ABBREVIATIONS = (
    "",
    "A",  # too short
    "AB" * 6,  # too long
    "3",  # disallowed: exclusively composed of digits
    "A!B!C!",
    "H.P.!",
    "abc",  # disallowed: all lowercase
    "house",
    "äbç",  # disallowed: all lowercase (unicode)
    "CRIS-CODE",  # hyphens not allowed
)


@pytest.mark.parametrize(
    "s,expected",
    chain(zip(_ABBREVIATIONS, repeat(True)), zip(_NON_ABBREVIATIONS, repeat(False))),
)
def test_is_abbreviation(s: str, expected: bool):
    """Test the _is_abbreviation() function."""
    assert _is_abbreviation(s) == expected
