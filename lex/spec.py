"""Token specifications. Order in DEFAULT_SPEC == priority (earlier wins on ties)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenSpec:
    name: str
    regex: str


DEFAULT_SPEC: list[TokenSpec] = [
    TokenSpec("SPACE",       "( |\n|\t)+"),

    TokenSpec("KW_IF",       "if"),
    TokenSpec("KW_THEN",     "then"),
    TokenSpec("KW_ELSE",     "else"),
    TokenSpec("KW_WHILE",    "while"),
    TokenSpec("KW_RETURN",   "return"),
    TokenSpec("KW_FOR",      "for"),
    TokenSpec("KW_BREAK",    "break"),
    TokenSpec("KW_CONTINUE", "continue"),
    TokenSpec("KW_INT",      "int"),
    TokenSpec("KW_FLOAT",    "float"),

    TokenSpec("ID",  "([A-Z]|[a-z])(([A-Z]|[a-z])|([0-9]|_))*"),
    TokenSpec("NUM", r"[0-9]+(\.[0-9]+)?"),

    # Two-char operators come before their one-char prefixes so the longest match wins.
    TokenSpec("EQ",       "=="),
    TokenSpec("NEQ",      "!="),
    TokenSpec("LTE",      "<="),
    TokenSpec("GTE",      ">="),
    TokenSpec("ASSIGN",   "="),
    TokenSpec("LT",       "<"),
    TokenSpec("GT",       ">"),
    TokenSpec("OP_PLUS",  r"\+"),
    TokenSpec("OP_MINUS", r"\-"),
    TokenSpec("OP_MULT",  r"\*"),
    TokenSpec("OP_DIV",   "/"),

    TokenSpec("LPAREN", r"\("),
    TokenSpec("RPAREN", r"\)"),
    TokenSpec("LBRACE", "{"),
    TokenSpec("RBRACE", "}"),
    TokenSpec("SEMI",   ";"),
    TokenSpec("COMMA",  ","),
]
