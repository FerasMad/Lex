import pytest

from lex.combine import combine
from lex.dfa import build
from lex.simulate import LexError, simulate
from lex.spec import TokenSpec


def _dfa(specs):
    return build(combine(specs))


def test_maximal_munch_prefers_longer_match():
    """'==' must beat '=' even though '=' is also accepting."""
    dfa = _dfa([TokenSpec("EQ", "=="), TokenSpec("ASSIGN", "=")])
    [tok] = simulate(dfa, "==")
    assert tok.type == "EQ"
    assert tok.value == "=="


def test_falls_back_to_shorter_match_when_long_one_breaks():
    dfa = _dfa([
        TokenSpec("EQ", "=="),
        TokenSpec("ASSIGN", "="),
        TokenSpec("SPACE", " +"),
    ])
    tokens = simulate(dfa, "= =")
    assert [t.type for t in tokens] == ["ASSIGN", "ASSIGN"]
    assert tokens[0].column == 1
    assert tokens[1].column == 3


def test_line_and_column_track_across_newlines():
    dfa = _dfa([
        TokenSpec("ID", "([a-z])+"),
        TokenSpec("SPACE", "( |\n)+"),
    ])
    tokens = simulate(dfa, "ab\ncd")
    assert tokens[0].line == 1 and tokens[0].column == 1
    assert tokens[1].line == 2 and tokens[1].column == 1


def test_lex_error_carries_position():
    dfa = _dfa([TokenSpec("ID", "([a-z])+")])
    with pytest.raises(LexError) as info:
        simulate(dfa, "ab$cd")
    err = info.value
    assert err.char == "$"
    assert err.line == 1 and err.column == 3


def test_skip_token_is_dropped_from_output():
    dfa = _dfa([
        TokenSpec("ID", "([a-z])+"),
        TokenSpec("SPACE", " +"),
    ])
    tokens = simulate(dfa, "a b c")
    assert [t.value for t in tokens] == ["a", "b", "c"]
