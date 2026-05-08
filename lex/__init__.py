"""CSC339 Lexical Analyzer.

Pipeline: Regex -> ε-NFA (Thompson) -> DFA (subset construction) -> Simulation (maximal munch).
"""

from .cli import run
from .simulate import LexError, Token
from .spec import DEFAULT_SPEC, TokenSpec

__version__ = "0.1.0"

__all__ = ["DEFAULT_SPEC", "LexError", "Token", "TokenSpec", "run"]
