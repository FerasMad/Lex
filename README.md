# Lexical Analyzer

**Course:** CSC339 — Theory of Computation, King Saud University, 1446/47 AH
**Team:**
Feras Madkhali - 444102819, Abdulmajeed Alwardi, Abdulaziz Alabdullatif

A lexical analyzer built from scratch in Python. No regex library is used —
the project ingests a list of `(name, regex)` pairs and walks them through
the four-stage pipeline:

```
regex source → ε-NFA (Thompson) → DFA (subset construction) → maximal-munch scan
```

## Layout

```
lex/
  spec.py           TokenSpec dataclass + DEFAULT_SPEC list (priority = order)
  regex_parser.py   tokenize, character-class expansion, infix → postfix
  nfa.py            State + Thompson constructors (atom/concat/union/*/+/?)
  combine.py        merge per-rule NFAs under one ε-start state
  dfa.py            DFAState, ε-closure, move, subset construction
  simulate.py       Token, LexError, maximal-munch loop with line/col tracking
  cli.py            argparse entry point — file mode + interactive REPL
samples/
  sample1.txt       the spec example
  sample2.txt       multi-line, every token kind, decimals
tests/              one test module per package module
docs/
  report.md         the full project report
```

## Install

```bash
python -m pip install -e .
```

The package itself has zero runtime dependencies; `pytest` is only needed
for the test suite.

## Run

**File mode:**

```bash
python -m lex samples/sample1.txt
```

**Interactive REPL** (no arguments):

```bash
python -m lex
```

In REPL mode, type code over multiple lines, then `END` on its own line
to lex it. `EXIT` quits.

## Example output

For `samples/sample1.txt`:

```
if x > y then {x=y; z=x-1} else x=y+5
```

```
Lexeme          Token           Position
'if'            KW_IF           Line 1, col 1
'x'             ID              Line 1, col 4
'>'             GT              Line 1, col 6
'y'             ID              Line 1, col 8
'then'          KW_THEN         Line 1, col 10
'{'             LBRACE          Line 1, col 15
'x'             ID              Line 1, col 16
'='             ASSIGN          Line 1, col 17
'y'             ID              Line 1, col 18
';'             SEMI            Line 1, col 19
'z'             ID              Line 1, col 21
'='             ASSIGN          Line 1, col 22
'x'             ID              Line 1, col 23
'-'             OP_MINUS        Line 1, col 24
'1'             NUM             Line 1, col 25
'}'             RBRACE          Line 1, col 26
'else'          KW_ELSE         Line 1, col 28
'x'             ID              Line 1, col 33
'='             ASSIGN          Line 1, col 34
'y'             ID              Line 1, col 35
'+'             OP_PLUS         Line 1, col 36
'5'             NUM             Line 1, col 37

Lexing Completed
```

## Tests

```bash
python -m pytest tests/ -v
```

One file per package module plus `test_end_to_end.py`, which asserts the
spec example produces the exact expected token list.

## Report

The full project report is in [docs/report.md](docs/report.md). It covers
all eleven sections required by the project spec — pseudocode for every
algorithm, data structures, time/space cost, two captured sample runs,
and a User Manual appendix.
