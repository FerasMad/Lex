from lex.nfa import EPSILON, State, build
from lex.regex_parser import compile_regex


def _walk(start: State, text: str) -> bool:
    """Recursive NFA matcher for whole-string equality. Used to validate constructors."""
    frontier = _eclose({start})
    for ch in text:
        nxt: set[State] = set()
        for s in frontier:
            for t in s.transitions.get(ch, ()):
                nxt.add(t)
        frontier = _eclose(nxt)
        if not frontier:
            return False
    return any(s.is_accepting for s in frontier)


def _eclose(states: set[State]) -> set[State]:
    out = set(states)
    stack = list(states)
    while stack:
        s = stack.pop()
        for t in s.transitions.get(EPSILON, ()):
            if t not in out:
                out.add(t)
                stack.append(t)
    return out


def test_atom():
    start, end = build(["a"])
    assert _walk(start, "a")
    assert not _walk(start, "b")
    assert not _walk(start, "")


def test_concat():
    start, _ = build(compile_regex("ab"))
    assert _walk(start, "ab")
    assert not _walk(start, "a")
    assert not _walk(start, "ba")


def test_union():
    start, _ = build(compile_regex("a|b"))
    assert _walk(start, "a")
    assert _walk(start, "b")
    assert not _walk(start, "ab")


def test_star_matches_zero_and_more():
    start, _ = build(compile_regex("a*"))
    assert _walk(start, "")
    assert _walk(start, "a")
    assert _walk(start, "aaaa")


def test_plus_requires_at_least_one():
    start, _ = build(compile_regex("a+"))
    assert not _walk(start, "")
    assert _walk(start, "a")
    assert _walk(start, "aaa")


def test_optional_zero_or_one():
    start, _ = build(compile_regex("a?"))
    assert _walk(start, "")
    assert _walk(start, "a")
    assert not _walk(start, "aa")


def test_escape_strips_backslash():
    # The literal '+' character, not the regex operator.
    start, _ = build(compile_regex(r"\+"))
    assert _walk(start, "+")
    assert not _walk(start, "")
