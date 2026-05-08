"""Subset construction: combined NFA -> DFA with priority-resolved accepts."""

from .nfa import EPSILON, State


class DFAState:
    __slots__ = ("id", "nfa_states", "transitions", "is_accepting", "token_name")
    _counter = 0

    def __init__(self, nfa_states: frozenset[State]):
        self.id = DFAState._counter
        DFAState._counter += 1
        self.nfa_states = nfa_states
        self.transitions: dict[str, "DFAState"] = {}

        # If the closure reaches multiple accepting NFA states, the lowest priority
        # number wins — that is the rule that came first in the spec list.
        best = None
        for s in nfa_states:
            if s.is_accepting and (best is None or s.priority < best.priority):
                best = s
        self.is_accepting = best is not None
        self.token_name = best.token_name if best else None

    def __repr__(self) -> str:
        tag = f" {self.token_name}" if self.is_accepting else ""
        return f"<DFAState {self.id}{tag}>"


def epsilon_closure(states: set[State]) -> set[State]:
    """All NFA states reachable from ``states`` via ε-transitions only."""
    closure = set(states)
    stack = list(states)
    while stack:
        s = stack.pop()
        for t in s.transitions.get(EPSILON, ()):
            if t not in closure:
                closure.add(t)
                stack.append(t)
    return closure


def move(states: set[State], symbol: str) -> set[State]:
    """All NFA states reachable from ``states`` by consuming exactly ``symbol``."""
    out: set[State] = set()
    for s in states:
        out.update(s.transitions.get(symbol, ()))
    return out


def alphabet_of(start: State) -> set[str]:
    """Every non-ε symbol that appears anywhere in the NFA reachable from ``start``."""
    seen: set[State] = set()
    alpha: set[str] = set()
    stack = [start]
    while stack:
        s = stack.pop()
        if s in seen:
            continue
        seen.add(s)
        for sym, targets in s.transitions.items():
            if sym != EPSILON:
                alpha.add(sym)
            for t in targets:
                if t not in seen:
                    stack.append(t)
    return alpha


def build(nfa_start: State) -> DFAState:
    """Subset construction. Returns the start state of the new DFA."""
    DFAState._counter = 0
    alphabet = alphabet_of(nfa_start)

    start_set = frozenset(epsilon_closure({nfa_start}))
    start = DFAState(start_set)
    table: dict[frozenset[State], DFAState] = {start_set: start}
    pending = [start]

    while pending:
        current = pending.pop(0)
        for sym in alphabet:
            target = move(set(current.nfa_states), sym)
            if not target:
                continue
            closed = frozenset(epsilon_closure(target))
            if closed not in table:
                table[closed] = DFAState(closed)
                pending.append(table[closed])
            current.transitions[sym] = table[closed]

    return start
