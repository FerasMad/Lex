import unittest
from lexical_analyzer import (
    State,
    DFAState,
    TokenRule,
    Token,
    tokenize_regex,
    insert_concatenation,
    infix_to_postfix,
    create_base_nfa,
    concatenate_nfas,
    union_nfas,
    kleene_star_nfa,
    plus_nfa,
    optional_nfa,
    get_epsilon_closure,
    get_alphabet,
    get_move,
    build_dfa,
    build_nfa,
    combine_nfas,
)


class TestStates(unittest.TestCase):
    """Tests the fundamental NFA and DFA State structures."""

    def test_state_creation_and_transitions(self):
        # Create a non-accepting state
        state1 = State()
        self.assertFalse(state1.is_accepting)
        self.assertIsNone(state1.token_name)

        # Create an accepting state
        state2 = State(is_accepting=True, token_name="KW_IF", priority=1)
        self.assertTrue(state2.is_accepting)
        self.assertEqual(state2.token_name, "KW_IF")

        # Test adding transitions
        state1.add_transition("a", state2)
        self.assertIn("a", state1.transitions)
        self.assertEqual(state1.transitions["a"][0], state2)

    def test_dfa_state_priority_resolution(self):
        """
        Ensures that when a DFA state contains multiple accepting NFA states,
        it inherits the token_name of the one with the lowest priority number.
        """
        # Create an NFA state that accepts an Identifier (lower priority = higher number)
        nfa_id_accepting = State(is_accepting=True, token_name="ID", priority=5)
        # Create an NFA state that accepts a Keyword (higher priority = lower number)
        nfa_kw_accepting = State(is_accepting=True, token_name="KW_IF", priority=1)
        # Create a non-accepting state just to mix it in
        nfa_normal = State()

        # Combine them into a single DFA state
        dfa_state = DFAState([nfa_id_accepting, nfa_kw_accepting, nfa_normal])

        # The DFA state MUST accept, and MUST be KW_IF because 1 < 5
        self.assertTrue(dfa_state.is_accepting)
        self.assertEqual(dfa_state.token_name, "KW_IF")


class TestRegexPipeline(unittest.TestCase):
    """Tests the functions that process the raw regex string into postfix tokens."""

    def test_tokenize_regex_basic(self):
        # Test basic characters
        tokens = tokenize_regex("abc")
        self.assertEqual(tokens, ["a", "b", "c"])

    def test_tokenize_regex_escapes(self):
        # Test escaped operators (e.g., matching a literal plus sign)
        tokens = tokenize_regex(r"\+")
        self.assertEqual(tokens, [r"\+"])

    def test_tokenize_regex_ranges(self):
        # Test that [a-c] expands to (a|b|c)
        tokens = tokenize_regex("[a-c]")
        self.assertEqual(tokens, ["(", "a", "|", "b", "|", "c", ")"])

    def test_insert_concatenation(self):
        # Test that 'a' followed by 'b' gets a concatenation operator '•'
        tokens = ["a", "b", "+", "c"]
        result = insert_concatenation(tokens)
        self.assertEqual(result, ["a", "•", "b", "+", "•", "c"])

    def test_infix_to_postfix(self):
        # Test shunting yard algorithm
        # a•b|c -> ab•c|
        tokens = ["a", "•", "b", "|", "c"]
        postfix = infix_to_postfix(tokens)
        self.assertEqual(postfix, ["a", "b", "•", "c", "|"])

        # Test with parentheses
        # (a|b)•c -> ab|c•
        tokens2 = ["(", "a", "|", "b", ")", "•", "c"]
        postfix2 = infix_to_postfix(tokens2)
        self.assertEqual(postfix2, ["a", "b", "|", "c", "•"])


class TestNFAOperations(unittest.TestCase):
    """Tests the base Thompson's Construction NFA builders."""

    def test_create_base_nfa(self):
        start, end = create_base_nfa(["a"])
        self.assertFalse(start.is_accepting)
        self.assertTrue(end.is_accepting)
        self.assertIn("a", start.transitions)
        self.assertEqual(start.transitions["a"][0], end)

    def test_concatenate_nfas(self):
        nfa1_start, nfa1_end = create_base_nfa(["a"])
        nfa2_start, nfa2_end = create_base_nfa(["b"])

        start, end = concatenate_nfas((nfa1_start, nfa1_end), (nfa2_start, nfa2_end))

        # nfa1_end should no longer be accepting
        self.assertFalse(nfa1_end.is_accepting)
        # new end should be accepting
        self.assertTrue(end.is_accepting)
        # nfa1_end should have an epsilon transition to nfa2_start
        self.assertIn("epsilon", nfa1_end.transitions)
        self.assertEqual(nfa1_end.transitions["epsilon"][0], nfa2_start)

    def test_kleene_star_nfa(self):
        base_nfa = create_base_nfa(["a"])
        start, end = kleene_star_nfa(base_nfa)

        self.assertTrue(end.is_accepting)
        # New start should skip to end via epsilon
        self.assertIn("epsilon", start.transitions)
        self.assertIn(end, start.transitions["epsilon"])


class TestSubsetHelpers(unittest.TestCase):
    """Tests the graph traversal algorithms used for NFA to DFA conversion."""

    def test_get_alphabet(self):
        start, end = create_base_nfa(["a"])
        start.add_transition("b", end)
        start.add_transition("epsilon", end)  # Should be ignored

        alphabet = get_alphabet(start)
        self.assertIn("a", alphabet)
        self.assertIn("b", alphabet)
        self.assertNotIn("epsilon", alphabet)

    def test_get_epsilon_closure(self):
        s1 = State()
        s2 = State()
        s3 = State()

        # s1 -> s2 via epsilon, s2 -> s3 via epsilon
        s1.add_transition("epsilon", s2)
        s2.add_transition("epsilon", s3)

        # The closure of s1 should include s1 itself, s2, and s3
        closure = get_epsilon_closure([s1])
        self.assertIn(s1, closure)
        self.assertIn(s2, closure)
        self.assertIn(s3, closure)
        self.assertEqual(len(closure), 3)

    def test_get_move(self):
        s1 = State()
        s2 = State()
        s3 = State()

        s1.add_transition("a", s2)
        s1.add_transition("a", s3)
        s1.add_transition("b", s2)

        # Moving from s1 on 'a' should yield both s2 and s3
        move_a = get_move([s1], "a")
        self.assertIn(s2, move_a)
        self.assertIn(s3, move_a)
        self.assertEqual(len(move_a), 2)


class TestDFAConstruction(unittest.TestCase):
    """Tests the full NFA to DFA determinization process."""

    def test_build_dfa_union(self):
        # Build an NFA for "a" | "b"
        nfa_a_start, nfa_a_end = create_base_nfa(["a"])
        nfa_b_start, nfa_b_end = create_base_nfa(["b"])

        # Tag the ends so the DFA knows they accept
        nfa_a_end.is_accepting = True
        nfa_a_end.token_name = "TOKEN_A"
        nfa_a_end.priority = 1

        nfa_b_end.is_accepting = True
        nfa_b_end.token_name = "TOKEN_B"
        nfa_b_end.priority = 2

        # Combine them into a global start state
        global_start = combine_nfas(
            [
                (nfa_a_start, nfa_a_end, "TOKEN_A", 1),
                (nfa_b_start, nfa_b_end, "TOKEN_B", 2),
            ]
        )

        # Convert to DFA
        dfa_start = build_dfa(global_start)

        # Verification:
        # 1. The start state should NOT be accepting (epsilon closure doesn't reach the ends)
        self.assertFalse(dfa_start.is_accepting)

        # 2. It should have deterministic transitions for 'a' and 'b'
        self.assertIn("a", dfa_start.transitions)
        self.assertIn("b", dfa_start.transitions)

        # 3. The state reached by 'a' should be an accepting state for TOKEN_A
        state_after_a = dfa_start.transitions["a"]
        self.assertTrue(state_after_a.is_accepting)
        self.assertEqual(state_after_a.token_name, "TOKEN_A")


from lexical_analyzer import simulate_lexer


class TestLexerSimulation(unittest.TestCase):
    """Tests the Maximal Munch algorithm and line/column tracking."""

    def test_simulate_lexer_maximal_munch(self):
        # We will manually construct a tiny DFA to test Maximal Munch
        # It accepts "=" (ASSIGN) and "==" (EQ, priority over ASSIGN)

        dfa_start = DFAState([])
        dfa_eq_1 = DFAState([])  # Reached after "="
        dfa_eq_1.is_accepting = True
        dfa_eq_1.token_name = "ASSIGN"

        dfa_eq_2 = DFAState([])  # Reached after "=="
        dfa_eq_2.is_accepting = True
        dfa_eq_2.token_name = "EQ"

        dfa_start.transitions["="] = dfa_eq_1
        dfa_eq_1.transitions["="] = dfa_eq_2

        # Test 1: Maximal Munch should prefer "==" over "="
        tokens1 = simulate_lexer(dfa_start, "==")
        self.assertEqual(len(tokens1), 1)
        self.assertEqual(tokens1[0].type, "EQ")

        # Test 2: It should fallback to "=" if the second character isn't "="
        # Let's add a dummy space token state to test token sequence
        dfa_space = DFAState([])
        dfa_space.is_accepting = True
        dfa_space.token_name = "SPACE"
        dfa_start.transitions[" "] = dfa_space

        # Input "= =" should yield [ASSIGN, ASSIGN] (space is ignored by the lexer's append logic)
        tokens2 = simulate_lexer(dfa_start, "= =")
        self.assertEqual(len(tokens2), 2)
        self.assertEqual(tokens2[0].type, "ASSIGN")
        self.assertEqual(tokens2[1].type, "ASSIGN")

        # Test 3: Check column tracking
        self.assertEqual(tokens2[0].column, 1)  # First '='
        self.assertEqual(tokens2[1].column, 3)  # Second '='


if __name__ == "__main__":
    unittest.main()
