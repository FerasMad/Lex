"""End-to-end checks against the spec example and a multiline sample."""

import pytest

from lex import LexError, run


SPEC_EXAMPLE = "if x > y then {x=y; z=x-1} else x=y+5"

EXPECTED = [
    ("if",   "KW_IF",    1,  1),
    ("x",    "ID",       1,  4),
    (">",    "GT",       1,  6),
    ("y",    "ID",       1,  8),
    ("then", "KW_THEN",  1, 10),
    ("{",    "LBRACE",   1, 15),
    ("x",    "ID",       1, 16),
    ("=",    "ASSIGN",   1, 17),
    ("y",    "ID",       1, 18),
    (";",    "SEMI",     1, 19),
    ("z",    "ID",       1, 21),
    ("=",    "ASSIGN",   1, 22),
    ("x",    "ID",       1, 23),
    ("-",    "OP_MINUS", 1, 24),
    ("1",    "NUM",      1, 25),
    ("}",    "RBRACE",   1, 26),
    ("else", "KW_ELSE",  1, 28),
    ("x",    "ID",       1, 33),
    ("=",    "ASSIGN",   1, 34),
    ("y",    "ID",       1, 35),
    ("+",    "OP_PLUS",  1, 36),
    ("5",    "NUM",      1, 37),
]


def test_spec_example_matches_expected_table():
    tokens = run(SPEC_EXAMPLE)
    actual = [(t.value, t.type, t.line, t.column) for t in tokens]
    assert actual == EXPECTED


def test_iff_stays_id_not_keyword():
    """The 'if' prefix must not gobble; 'iff' is an identifier."""
    [tok] = run("iff")
    assert tok.type == "ID"
    assert tok.value == "iff"


def test_decimal_numbers_lex_as_num():
    tokens = run("3.14 + 2")
    assert [(t.value, t.type) for t in tokens] == [
        ("3.14", "NUM"),
        ("+", "OP_PLUS"),
        ("2", "NUM"),
    ]


def test_multiline_input_tracks_lines():
    src = "x = 1\ny = 2"
    tokens = run(src)
    assert tokens[0].line == 1 and tokens[0].column == 1   # x
    assert tokens[3].line == 2 and tokens[3].column == 1   # y


def test_illegal_character_raises_with_position():
    with pytest.raises(LexError) as info:
        run("x = $")
    err = info.value
    assert err.char == "$"
    assert err.line == 1
    assert err.column == 5
