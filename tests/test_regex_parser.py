import pytest

from lex.regex_parser import CONCAT, compile_regex, insert_concat, to_postfix, tokenize


def test_tokenize_literals():
    assert tokenize("abc") == ["a", "b", "c"]


def test_tokenize_keeps_escapes_as_two_char_tokens():
    assert tokenize(r"\+") == [r"\+"]
    assert tokenize(r"a\.b") == ["a", r"\.", "b"]


def test_tokenize_expands_range():
    assert tokenize("[a-c]") == ["(", "a", "|", "b", "|", "c", ")"]


def test_tokenize_expands_mixed_class():
    # individual chars and a range mixed in the same class
    assert tokenize("[ab0-2]") == ["(", "a", "|", "b", "|", "0", "|", "1", "|", "2", ")"]


def test_tokenize_rejects_empty_and_trailing_backslash():
    with pytest.raises(SyntaxError):
        tokenize("")
    with pytest.raises(SyntaxError):
        tokenize("a\\")


def test_tokenize_rejects_unclosed_class():
    with pytest.raises(SyntaxError):
        tokenize("[abc")


def test_tokenize_rejects_reversed_range():
    with pytest.raises(SyntaxError):
        tokenize("[z-a]")


def test_insert_concat_basic():
    # 'ab+c' -> a • b + • c   (concat between adjacent atoms, none before +)
    assert insert_concat(["a", "b", "+", "c"]) == ["a", CONCAT, "b", "+", CONCAT, "c"]


def test_insert_concat_skips_around_operators_and_groups():
    assert insert_concat(["(", "a", "|", "b", ")"]) == ["(", "a", "|", "b", ")"]


def test_to_postfix_simple():
    # a • b | c  ->  a b • c |
    assert to_postfix(["a", CONCAT, "b", "|", "c"]) == ["a", "b", CONCAT, "c", "|"]


def test_to_postfix_handles_parens():
    # (a|b) • c  ->  a b | c •
    assert to_postfix(["(", "a", "|", "b", ")", CONCAT, "c"]) == ["a", "b", "|", "c", CONCAT]


def test_to_postfix_rejects_mismatched_parens():
    with pytest.raises(SyntaxError):
        to_postfix(["(", "a"])
    with pytest.raises(SyntaxError):
        to_postfix(["a", ")"])


def test_compile_regex_full_pipeline():
    # End-to-end: 'a(b|c)*' -> a b c | * •
    assert compile_regex("a(b|c)*") == ["a", "b", "c", "|", "*", CONCAT]
