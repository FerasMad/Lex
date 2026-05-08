"""Command-line entry point and the high-level ``run`` helper."""

import argparse
import sys

from . import combine, dfa
from .simulate import LexError, Token, format_tokens, simulate
from .spec import DEFAULT_SPEC, TokenSpec


def run(text: str, specs: list[TokenSpec] | None = None) -> list[Token]:
    """Compile the spec to a DFA, scan ``text``, return the tokens."""
    nfa_start = combine.combine(specs or DEFAULT_SPEC)
    dfa_start = dfa.build(nfa_start)
    return simulate(dfa_start, text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lex", description="CSC339 lexical analyzer.")
    parser.add_argument("path", nargs="?", help="source file; omit for interactive REPL")
    args = parser.parse_args(argv)

    if args.path:
        return _run_file(args.path)
    return _repl()


def _run_file(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    print(f"--- Lexing file: {path} ---\n")
    return _lex_and_print(text)


def _repl() -> int:
    print("--- Interactive lexical analyzer ---")
    print("Enter code; type 'END' on its own line to lex, 'EXIT' to quit.\n")

    while True:
        try:
            first = input("lex> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if first.strip().upper() == "EXIT":
            return 0
        if first.strip().upper() == "END":
            continue

        lines = [first]
        while True:
            try:
                line = input("...  ")
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if line.strip().upper() == "END":
                break
            lines.append(line)

        text = "\n".join(lines)
        if not text.strip():
            continue
        _lex_and_print(text)
        print()


def _lex_and_print(text: str) -> int:
    try:
        tokens = run(text)
    except LexError as e:
        print(format_tokens([]))  # header only
        print(f"\nLexing Error: unrecognized {e.char!r} at line {e.line}, col {e.column}")
        return 1

    print(format_tokens(tokens))
    print("\nLexing Completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
