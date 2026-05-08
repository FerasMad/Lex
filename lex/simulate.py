"""Maximal-munch simulation of a labelled DFA."""

from dataclasses import dataclass

from .dfa import DFAState

WHITESPACE_TOKEN = "SPACE"


@dataclass(frozen=True, slots=True)
class Token:
    type: str
    value: str
    line: int
    column: int


class LexError(Exception):
    """Raised on the first character that has no DFA transition."""

    def __init__(self, char: str, line: int, column: int):
        super().__init__(f"unrecognized {char!r} at line {line}, col {column}")
        self.char = char
        self.line = line
        self.column = column


def simulate(dfa: DFAState, text: str, *, skip: str = WHITESPACE_TOKEN) -> list[Token]:
    """Scan ``text`` and return the token list. Raises ``LexError`` on a bad char.

    Tokens whose type equals ``skip`` are dropped from the output (whitespace by
    default). Pass ``skip=None`` to keep everything.
    """
    tokens: list[Token] = []
    pos = 0
    line, col = 1, 1

    while pos < len(text):
        start_line, start_col = line, col
        last_accept_pos = -1
        last_accept_name: str | None = None

        state = dfa
        i = pos
        while i < len(text):
            nxt = state.transitions.get(text[i])
            if nxt is None:
                break
            state = nxt
            if state.is_accepting:
                last_accept_pos = i
                last_accept_name = state.token_name
            i += 1

        if last_accept_pos == -1:
            raise LexError(text[pos], line, col)

        lexeme = text[pos:last_accept_pos + 1]
        if last_accept_name != skip:
            tokens.append(Token(last_accept_name, lexeme, start_line, start_col))

        for ch in lexeme:
            if ch == "\n":
                line += 1
                col = 1
            else:
                col += 1
        pos = last_accept_pos + 1

    return tokens


def format_tokens(tokens: list[Token]) -> str:
    """Three-column ``Lexeme | Token | Position`` table matching the spec example."""
    lines = [f"{'Lexeme':<15} {'Token':<15} Position"]
    for t in tokens:
        lines.append(f"{repr(t.value):<15} {t.type:<15} Line {t.line}, col {t.column}")
    return "\n".join(lines)
