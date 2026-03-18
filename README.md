# Lex — Lexical Analyzer

A lexical analyzer built from scratch in Python. Takes a list of token specifications and an input program, then produces a stream of tokens using the full Regex → NFA → DFA → Simulation pipeline.

**Course:** CSC339 Theory of Computation — King Saud University, 2026
**Team:** Feras, Abdulmajid, Abdullatif

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the lexer on an input file
python main.py tests/sample_input_1.txt
```

## How to Test

```bash
pytest tests/
```

## Project Structure

```
automaton.py       # data structures (NFAState, DFAState, Token, AST nodes)
token_spec.py      # token definitions and priority order
regex_parser.py    # converts regex string to AST
char_class.py      # expands character classes like [a-z]
nfa_builder.py     # builds NFA from AST using Thompson's construction
dfa_builder.py     # converts NFA to DFA using subset construction
dfa_simulator.py   # simulates DFA on input using maximal munch
lexer.py           # ties the full pipeline together
main.py            # command-line entry point
tests/             # unit tests and sample inputs
```
