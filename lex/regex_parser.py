"""Regex front end: raw string -> token list -> postfix.

Three passes, intentionally separate so each can be unit-tested:
    tokenize -> insert_concat -> infix_to_postfix
"""

CONCAT = "•"  # bullet — not a regex operator and not a NUM character, so it is safe to inject
_PRECEDENCE = {"*": 2, "+": 2, "?": 2, CONCAT: 1, "|": 0}


def tokenize(regex: str) -> list[str]:
    """Split a regex into a flat list of literals and operators.

    Character classes ``[a-z]`` are expanded to ``(a|b|...|z)``.
    Escapes like ``\\+`` are kept as the two-character token ``"\\+"``;
    the NFA stage strips the backslash.
    """
    if not regex:
        raise SyntaxError("empty regex")
    if regex.endswith("\\"):
        raise SyntaxError("trailing backslash")

    out: list[str] = []
    i = 0
    while i < len(regex):
        c = regex[i]

        if c == "\\":
            out.append(regex[i:i + 2])
            i += 2
            continue

        if c == "[":
            out.extend(_expand_class(regex, i))
            i = regex.index("]", i) + 1
            continue

        out.append(c)
        i += 1

    return out


def _expand_class(regex: str, open_idx: int) -> list[str]:
    """Return the ``(a|b|...)`` token list for a bracket class starting at ``open_idx``."""
    end = regex.find("]", open_idx)
    if end == -1:
        raise SyntaxError("unclosed character class")

    body = regex[open_idx + 1:end]
    chars: list[str] = []
    j = 0
    while j < len(body):
        if j + 2 < len(body) and body[j + 1] == "-":
            lo, hi = body[j], body[j + 2]
            if ord(lo) > ord(hi):
                raise SyntaxError(f"reversed range: {lo}-{hi}")
            chars.extend(chr(k) for k in range(ord(lo), ord(hi) + 1))
            j += 3
        else:
            chars.append(body[j])
            j += 1

    pieces: list[str] = ["("]
    for k, ch in enumerate(chars):
        pieces.append(ch)
        if k < len(chars) - 1:
            pieces.append("|")
    pieces.append(")")
    return pieces


def insert_concat(tokens: list[str]) -> list[str]:
    """Insert the explicit concatenation operator between adjacent atoms."""
    out: list[str] = []
    for i, tok in enumerate(tokens):
        out.append(tok)
        if i + 1 == len(tokens):
            continue
        nxt = tokens[i + 1]
        if tok in ("(", "|"):
            continue
        if nxt in ("*", "+", "?", "|", ")"):
            continue
        out.append(CONCAT)
    return out


def to_postfix(tokens: list[str]) -> list[str]:
    """Shunting-yard: infix regex tokens -> postfix."""
    out: list[str] = []
    ops: list[str] = []

    for tok in tokens:
        if tok == "(":
            ops.append(tok)
        elif tok == ")":
            while ops and ops[-1] != "(":
                out.append(ops.pop())
            if not ops:
                raise SyntaxError("mismatched parentheses")
            ops.pop()
        elif tok in _PRECEDENCE:
            while ops and ops[-1] != "(" and _PRECEDENCE.get(ops[-1], -1) >= _PRECEDENCE[tok]:
                out.append(ops.pop())
            ops.append(tok)
        else:
            out.append(tok)

    while ops:
        op = ops.pop()
        if op in ("(", ")"):
            raise SyntaxError("mismatched parentheses")
        out.append(op)

    return out


def compile_regex(regex: str) -> list[str]:
    """Convenience: ``tokenize -> insert_concat -> to_postfix``."""
    return to_postfix(insert_concat(tokenize(regex)))
