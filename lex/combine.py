"""Glue per-rule NFAs into one combined NFA under a single start state."""

from . import nfa, regex_parser
from .nfa import EPSILON, NFA, State
from .spec import TokenSpec


def combine(specs: list[TokenSpec]) -> State:
    """Build one NFA from a priority-ordered spec list.

    Each rule's NFA is constructed independently, its accepting state is tagged
    with the token name and the rule's index (used as priority on ties), and a
    fresh ε-edge is added from a global start state into each rule's start.
    """
    start = State()

    for priority, spec in enumerate(specs):
        postfix = regex_parser.compile_regex(spec.regex)
        rule_start, rule_end = nfa.build(postfix)
        rule_end.is_accepting = True
        rule_end.token_name = spec.name
        rule_end.priority = priority
        start.add(EPSILON, rule_start)

    return start


def combine_nfas(rules: list[tuple[NFA, str, int]]) -> State:
    """Lower-level form: take pre-built NFAs and glue them under one start."""
    start = State()
    for (rule_start, rule_end), name, priority in rules:
        rule_end.is_accepting = True
        rule_end.token_name = name
        rule_end.priority = priority
        start.add(EPSILON, rule_start)
    return start
