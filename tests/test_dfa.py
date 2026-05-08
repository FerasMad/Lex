from lex.combine import combine
from lex.dfa import alphabet_of, build, epsilon_closure, move
from lex.nfa import EPSILON, State
from lex.spec import TokenSpec


def test_epsilon_closure_walks_chains():
    a, b, c = State(), State(), State()
    a.add(EPSILON, b)
    b.add(EPSILON, c)
    closure = epsilon_closure({a})
    assert closure == {a, b, c}


def test_move_returns_only_direct_targets():
    a, b, c = State(), State(), State()
    a.add("x", b)
    a.add("x", c)
    a.add("y", b)
    assert move({a}, "x") == {b, c}
    assert move({a}, "y") == {b}
    assert move({a}, "z") == set()


def test_alphabet_excludes_epsilon():
    a, b = State(), State()
    a.add("x", b)
    a.add(EPSILON, b)
    assert alphabet_of(a) == {"x"}


def test_priority_tiebreak_keyword_beats_id():
    """When 'if' matches both KW_IF and ID, the earlier rule wins."""
    nfa_start = combine([
        TokenSpec("KW_IF", "if"),
        TokenSpec("ID", "([A-Z]|[a-z])(([A-Z]|[a-z])|[0-9])*"),
    ])
    dfa_start = build(nfa_start)

    state = dfa_start
    for ch in "if":
        state = state.transitions[ch]
    assert state.is_accepting
    assert state.token_name == "KW_IF"


def test_id_still_wins_when_keyword_does_not_match():
    """'iff' is not a keyword — it should fall through to ID."""
    nfa_start = combine([
        TokenSpec("KW_IF", "if"),
        TokenSpec("ID", "([A-Z]|[a-z])(([A-Z]|[a-z])|[0-9])*"),
    ])
    dfa_start = build(nfa_start)

    state = dfa_start
    for ch in "iff":
        state = state.transitions[ch]
    assert state.is_accepting
    assert state.token_name == "ID"


def test_subset_construction_dead_branches_have_no_transition():
    nfa_start = combine([TokenSpec("AB", "ab")])
    dfa_start = build(nfa_start)
    # 'a' is fine, but no transition for 'z' from the start
    assert "a" in dfa_start.transitions
    assert "z" not in dfa_start.transitions
