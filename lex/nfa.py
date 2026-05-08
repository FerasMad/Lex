"""Thompson construction. Builds an NFA from postfix regex tokens."""

from .regex_parser import CONCAT

EPSILON = "ε"
NFA = tuple["State", "State"]


class State:
    __slots__ = ("id", "is_accepting", "token_name", "priority", "transitions")
    _counter = 0

    def __init__(self, *, accepting: bool = False, token_name: str | None = None, priority: int | None = None):
        self.id = State._counter
        State._counter += 1
        self.is_accepting = accepting
        self.token_name = token_name
        self.priority = priority
        self.transitions: dict[str, list["State"]] = {}

    def add(self, symbol: str, target: "State") -> None:
        self.transitions.setdefault(symbol, []).append(target)

    def __repr__(self) -> str:
        tag = f" {self.token_name}" if self.is_accepting else ""
        return f"<State {self.id}{tag}>"


def build(postfix: list[str]) -> NFA:
    """Evaluate a postfix regex into an NFA fragment ``(start, accept)``."""
    stack: list[NFA] = []

    for tok in postfix:
        if tok == "*":
            stack.append(_star(stack.pop()))
        elif tok == "+":
            stack.append(_plus(stack.pop()))
        elif tok == "?":
            stack.append(_optional(stack.pop()))
        elif tok == CONCAT:
            b = stack.pop()
            a = stack.pop()
            stack.append(_concat(a, b))
        elif tok == "|":
            b = stack.pop()
            a = stack.pop()
            stack.append(_union(a, b))
        else:
            symbol = tok[1] if len(tok) == 2 and tok[0] == "\\" else tok
            stack.append(_atom(symbol))

    if len(stack) != 1:
        raise ValueError(f"malformed postfix; stack left with {len(stack)} items")
    return stack[0]


def _atom(symbol: str) -> NFA:
    s, e = State(), State(accepting=True)
    s.add(symbol, e)
    return s, e


def _concat(a: NFA, b: NFA) -> NFA:
    a_start, a_end = a
    b_start, b_end = b
    a_end.add(EPSILON, b_start)
    a_end.is_accepting = False
    return a_start, b_end


def _union(a: NFA, b: NFA) -> NFA:
    a_start, a_end = a
    b_start, b_end = b
    s, e = State(), State(accepting=True)
    s.add(EPSILON, a_start)
    s.add(EPSILON, b_start)
    a_end.add(EPSILON, e)
    b_end.add(EPSILON, e)
    a_end.is_accepting = False
    b_end.is_accepting = False
    return s, e


def _star(n: NFA) -> NFA:
    n_start, n_end = n
    s, e = State(), State(accepting=True)
    s.add(EPSILON, e)
    s.add(EPSILON, n_start)
    n_end.add(EPSILON, n_start)
    n_end.add(EPSILON, e)
    n_end.is_accepting = False
    return s, e


def _plus(n: NFA) -> NFA:
    n_start, n_end = n
    s, e = State(), State(accepting=True)
    s.add(EPSILON, n_start)
    n_end.add(EPSILON, n_start)
    n_end.add(EPSILON, e)
    n_end.is_accepting = False
    return s, e


def _optional(n: NFA) -> NFA:
    n_start, n_end = n
    s, e = State(), State(accepting=True)
    s.add(EPSILON, n_start)
    s.add(EPSILON, e)
    n_end.add(EPSILON, e)
    n_end.is_accepting = False
    return s, e
