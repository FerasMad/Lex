# Lexical analyzer for Python code
import sys


class TokenRule:
    """
    Specification for each token type, storing it's priority for tie-breaking when
    a string matches in more than one rules.
    """

    def __init__(self, name, regex, priority):
        self.name = name
        self.regex = regex
        self.priority = priority


class Token:
    """
    The token object which after the lexer successfully recognizes a lexeme,
    it stores it into this object along with its exact line and column position
    to be passed to the parser.
    """

    def __init__(self, type_name, value, line, column):
        self.type = type_name
        self.value = value
        self.line = line
        self.column = column


class State:
    """
    Represents a single state inside a NFA.
    _id_counter is a class level counter so every state gets a unique, readable ID for debugging.
    'transitions' is a dictionary where the key is the character or 'epsilon' and the value is a list of next state/s.
    """

    _id_counter = 0  # Class variable to assign unique IDs

    def __init__(self, is_accepting=False, token_name=None, priority=None):
        self.id = State._id_counter
        State._id_counter += 1

        self.is_accepting = is_accepting
        self.token_name = token_name
        self.priority = priority
        self.transitions = {}

    def add_transition(self, character, next_state):
        if character not in self.transitions:
            self.transitions[character] = []
        self.transitions[character].append(next_state)

    def __repr__(self):
        # Defines how the object looks when printed
        if self.is_accepting:
            return f"State_{self.id}(Accepts: {self.token_name})"
        return f"State_{self.id}"


class DFAState:
    """
    Represents a single DFA state: a set of NFA states.

    Note: If this DFA state contains multiple accepting NFA states,
    we loop through them and assign the token_name of the one with the
    lowest priority number, which appeared earlier than others.
    """

    _id_counter = 0

    def __init__(self, nfa_states):
        self.id = DFAState._id_counter
        DFAState._id_counter += 1

        self.nfa_states = frozenset(nfa_states)
        self.transitions = {}

        self.is_accepting = False
        self.token_name = None

        best_priority = float("inf")

        for state in self.nfa_states:
            if state.is_accepting:
                self.is_accepting = True
                if state.priority < best_priority:
                    best_priority = state.priority
                    self.token_name = state.token_name

    def __repr__(self):
        if self.is_accepting:
            return f"DFAState_{self.id}(Accepts: {self.token_name})"
        return f"DFAState_{self.id}"


def tokenize_regex(regex_string):
    """
    Step 1 in pipeline: Raw String to Tokens.
    This method takes the raw regex string and turns it into a clean list of characters and operators.
    it handle character classes like [a-z] or [0-9]. we detect the brackets, loop through the ASCII values,
    and manually expand them into basic unions: (a|b|c...|z). It also strips the backslash from escaped
    characters (like '\+') so they are treated as literal text.
    """

    if regex_string == "":
        raise SyntaxError("Empty string")

    if regex_string[-1] == "\\":
        raise SyntaxError("Invalid trailing backslash.")

    tokens = []
    i = 0

    while i < len(regex_string):
        char = regex_string[i]

        if "\\" == char and i + 1 < len(regex_string):
            char += regex_string[i + 1]
            tokens.append(char)
            i += 2
            continue

        elif char == "[":
            tokens.append("(")
            i += 1

            while i < len(regex_string) and regex_string[i] != "]":
                # --- PHASE 2: RANGE EXPANSION (e.g., a-z) ---
                # 1. Detection: Are we looking at a start char, followed by '-', followed by an end char?
                if (
                    i + 2 < len(regex_string)
                    and regex_string[i + 1] == "-"
                    and regex_string[i + 2] != "]"
                ):
                    start_char = regex_string[i]
                    end_char = regex_string[i + 2]

                    # 2. Validation: Prevent backwards ranges like [z-a]
                    if ord(start_char) > ord(end_char):
                        raise SyntaxError(
                            f"Invalid character range: {start_char}-{end_char}"
                        )

                    # 3 & 4. Generation and The Pipe Glue
                    for val in range(ord(start_char), ord(end_char) + 1):
                        tokens.append(chr(val))

                        # We need a pipe AFTER this character if:
                        # A) It's not the last character in our generated range.
                        # B) OR, it IS the last character in the range, but there are more characters
                        #    in the bracket after it (checked by looking at i+3).
                        if val != ord(end_char) or (
                            i + 3 < len(regex_string) and regex_string[i + 3] != "]"
                        ):
                            tokens.append("|")

                    # 5. The Jump: Skip the start_char, the hyphen, and the end_char
                    i += 3
                    continue

                tokens.append(regex_string[i])
                if i + 1 < len(regex_string) and regex_string[i + 1] != "]":
                    tokens.append("|")
                i += 1
                pass

            if i == len(regex_string):
                raise SyntaxError("Invalid syntax, no closing bracket.")

            tokens.append(")")

        else:
            tokens.append(char)

        i += 1

    return tokens


def insert_concatenation(tokens):
    """
    Step 2 in pipeline: Explicit Concatenation.
    In regex, 'ab' implicitly means 'a' concatenated with 'b'. But our math algorithms
    (Shunting Yard and Thompson's) need an actual operator to know when to link two states.
    This method looks at adjacent tokens and, if they are meant to be chained, inserts
    a special bullet '•' between them.
    (Note: We specifically used '•' instead of a normal period '.' so it doesn't collide
    with the actual decimal point in our NUM token regex).
    """

    result = []
    for i in range(len(tokens)):
        current_token = tokens[i]
        result.append(current_token)

        if i + 1 < len(tokens):
            next_token = tokens[i + 1]
            left_valid = current_token not in ["(", "|"]
            right_valid = next_token not in ["*", "+", "?", "|", ")"]

            if left_valid and right_valid:
                result.append("•")  # Changed from "." to avoid collisions
    return result


def infix_to_postfix(tokens):
    """
    Step 3 in pipeline: Shunting Yard Algorithm.
    Converts our normal "infix" regex (e.g., a•b|c) into "postfix" notation (e.g., ab•c|).
    Why do we do this? Because postfix is incredibly easy to evaluate from left to right
    using a single stack, which is exactly how we build our NFA in the next step.
    We use a dictionary called 'precedence' to tell the algorithm which operators
    (*, +, ?) should be processed before others (|).
    """

    output = []
    stack = []
    precedence = {"*": 2, "+": 2, "?": 2, "•": 1, "|": 0}  # Changed "." to "•"

    for token in tokens:
        if token == "(":
            stack.append(token)
        elif token == ")":
            while len(stack) > 0 and stack[-1] != "(":
                output.append(stack.pop())
            if len(stack) > 0:
                stack.pop()
        elif token in precedence:
            while (
                len(stack) > 0
                and stack[-1] != "("
                and precedence.get(stack[-1], -1) >= precedence[token]
            ):
                output.append(stack.pop())
            stack.append(token)
        else:
            output.append(token)

    while len(stack) > 0:
        op = stack.pop()
        if op in ["(", ")"]:
            raise SyntaxError(f"Mismatched parentheses in regex. Stack left with: {op}")
        output.append(op)

    return output


"""
Thompson's Construction
"""


def build_nfa(postfix):
    """
    Step 4 in pipeline: The NFA Stack Evaluator.
    This reads our postfix list left to right.
    - If it sees a character, it creates a basic 2-state NFA for it and pushes it onto the stack.
    - If it sees an operator (like *, +, or |), it pops the required number of NFAs off the stack,
      sticks them together using the helper functions below, and pushes the new combined NFA back on.
    When it's done, the single remaining item on the stack is the completed NFA for the entire token rule!
    """

    stack = []

    for char in postfix:
        if char in ["*", "+", "?"]:
            nfa = stack.pop()
            if char == "*":
                stack.append(kleene_star_nfa(nfa))
            elif char == "+":
                stack.append(plus_nfa(nfa))
            elif char == "?":
                stack.append(optional_nfa(nfa))

        elif char in ["•", "|"]:  # Changed "." to "•"
            nfa2 = stack.pop()
            nfa1 = stack.pop()

            if char == "•":
                stack.append(concatenate_nfas(nfa1, nfa2))
            elif char == "|":
                stack.append(union_nfas(nfa1, nfa2))

        else:
            # If it's an escaped character (e.g., "\+"), strip the "\"
            # so the DFA transitions on the exact literal character ("+")
            if len(char) == 2 and char.startswith("\\"):
                char = char[1]

            stack.append(create_base_nfa([char]))

    return stack.pop()


def create_base_nfa(charset):
    """
    The fundamental building block. Creates a Start state, an End state (accepting),
    and adds a transition between them for a specific character.
    """

    start_state = State()
    end_state = State(is_accepting=True)
    for character in charset:
        start_state.add_transition(character, end_state)

    return (start_state, end_state)


def concatenate_nfas(nfa1, nfa2):
    """
    Implements 'AB'.
    We take the End state of the first NFA, make it no longer accepting,
    and draw an epsilon (free) transition from it to the Start state of the second NFA.
    """

    nfa1_start, nfa1_end = nfa1
    nfa2_start, nfa2_end = nfa2
    nfa1_end.add_transition("epsilon", nfa2_start)
    nfa1_end.is_accepting = False
    return (nfa1_start, nfa2_end)


def union_nfas(nfa1, nfa2):
    """
    Implements 'A|B'.
    We create a brand new global Start state and a new global End state.
    The new Start splits into two paths via epsilons: one to NFA 1, one to NFA 2.
    The old End states of both NFAs get epsilons pointing to the new global End.
    """

    nfa1_start, nfa1_end = nfa1
    nfa2_start, nfa2_end = nfa2
    new_start = State()
    new_end = State(is_accepting=True)
    new_start.add_transition("epsilon", nfa1_start)
    new_start.add_transition("epsilon", nfa2_start)
    nfa1_end.add_transition("epsilon", new_end)
    nfa2_end.add_transition("epsilon", new_end)
    nfa1_end.is_accepting = False
    nfa2_end.is_accepting = False
    return (new_start, new_end)


def kleene_star_nfa(nfa):
    """
    Implements 'A*' (Zero or more times).
    - To handle "Zero": We add an epsilon skipping straight from the new Start to the new End.
    - To handle "More": We add an epsilon looping from the old End back to the old Start.
    """

    nfa_start, nfa_end = nfa
    new_start = State()
    new_end = State(is_accepting=True)
    new_start.add_transition("epsilon", new_end)
    new_start.add_transition("epsilon", nfa_start)
    nfa_end.add_transition("epsilon", nfa_start)
    nfa_end.add_transition("epsilon", new_end)
    nfa_end.is_accepting = False
    return (new_start, new_end)


def plus_nfa(nfa):
    """
    Implements 'A+' (One or more times).
    Structurally almost identical to Kleene Star (*), but we DO NOT include the epsilon
    transition skipping from the new Start to the new End. The machine MUST go through
    the NFA at least once.
    """

    nfa_start, nfa_end = nfa
    new_start = State()
    new_end = State(is_accepting=True)

    new_start.add_transition("epsilon", nfa_start)
    nfa_end.add_transition("epsilon", nfa_start)
    nfa_end.add_transition("epsilon", new_end)

    nfa_end.is_accepting = False

    return (new_start, new_end)


def optional_nfa(nfa):
    """
    Implements 'A?' (Zero or one time).
    We simply create an empty NFA that only accepts epsilon, and Union it with our target NFA.
    This gives the machine the choice to either process the NFA or bypass it completely.
    """

    epsilon_nfa = create_base_nfa(["epsilon"])
    return union_nfas(nfa, epsilon_nfa)


def combine_nfas(nfa_metadata_list):
    """
    The Grand Finale of NFA construction.
    Instead of having 15 separate state machines for our 15 token rules, we need one giant machine.
    This creates a single Global Start State and adds an epsilon transition pointing to the Start state
    of EVERY individual token's NFA.
    It also assigns the token's name and priority to its final accepting state here so we don't lose that info!
    """

    global_start = State()

    for nfa_start, nfa_end, token_name, priority in nfa_metadata_list:
        nfa_end.is_accepting = True
        nfa_end.token_name = token_name
        nfa_end.priority = priority

        global_start.add_transition("epsilon", nfa_start)

    return global_start


"""
Subset Construction
"""


def get_alphabet(nfa_start_state):
    """
    Helper for Subset Construction.
    Before we can convert our NFA to a DFA, we need to know exactly what characters
    trigger transitions in our machine (our "alphabet"). This traverses the entire
    NFA graph and collects every unique character (excluding epsilons) into a set.
    Dynamically finds all transition characters used in the NFA.
    """

    alphabet = set()
    visited = set()
    stack = [nfa_start_state]

    while len(stack) > 0:
        state = stack.pop()
        if state not in visited:
            visited.add(state)
            for char, next_states in state.transitions.items():
                if char != "epsilon":
                    alphabet.add(char)
                for ns in next_states:
                    if ns not in visited:
                        stack.append(ns)
    return alphabet


def get_epsilon_closure(states):
    """
    Helper for Subset Construction.
    Given a starting set of NFA states, what other states can be reached with 'epsilon'.
    This recursively follows all 'epsilon' transitions. In a DFA, a single state
    actually represents the entire epsilon closure of an NFA state.
    Returns all NFA states reachable via epsilon transitions.
    """

    closure = set(states)
    stack = list(states)
    while len(stack) > 0:
        current_state = stack.pop()
        if "epsilon" in current_state.transitions:
            for next_state in current_state.transitions["epsilon"]:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
    return closure


def get_move(states, char):
    """
    Helper for Subset Construction.
    Given a set of NFA states and a specific character, this finds all the immediate
    next states we can reach by consuming that exact character.
    (Note: This does not include the epsilon paths after the move; we call
    get_epsilon_closure on the result of get_move to get the full picture).
    Returns all NFA states reachable from a set of states via a specific character.
    """

    move_states = set()
    for state in states:
        if char in state.transitions:
            move_states.update(state.transitions[char])
    return move_states


def build_dfa(nfa_global_start):
    """
    Step 5 in pipeline: The Subset Construction Algorithm.
    This is where the magic happens. A computer cannot easily simulate an NFA because
    it has multiple paths for the same character. We convert it into a DFA where every
    character has exactly ONE deterministic path.

    Algorithm:
    1. The DFA start state is the epsilon-closure of the NFA start state.
    2. For every DFA state, we test every character in our alphabet using get_move().
    3. We take the epsilon-closure of those results. That new set of NFA states becomes
       a brand new DFA state.
    4. We repeat until no new DFA states are discovered.
    """

    alphabet = get_alphabet(nfa_global_start)

    # 1. The starting DFA state is the epsilon closure of the NFA start state
    start_closure = get_epsilon_closure([nfa_global_start])
    dfa_start = DFAState(start_closure)

    # Keep track of states we've created (using the frozenset of NFA states as the key)
    dfa_states = {dfa_start.nfa_states: dfa_start}

    # States we still need to compute transitions for
    unmarked_states = [dfa_start]

    while len(unmarked_states) > 0:
        current_dfa = unmarked_states.pop(0)

        for char in alphabet:
            # 2. Find where this character takes us in the NFA
            move_result = get_move(current_dfa.nfa_states, char)
            if not move_result:
                continue  # No transition for this character, leads to a dead state

            # 3. Find the epsilon closure of those resulting states
            closure_result = frozenset(get_epsilon_closure(move_result))

            # 4. If we haven't seen this set of NFA states before, it's a new DFA state!
            if closure_result not in dfa_states:
                new_dfa_state = DFAState(closure_result)
                dfa_states[closure_result] = new_dfa_state
                unmarked_states.append(new_dfa_state)

            # 5. Link the DFA states
            current_dfa.transitions[char] = dfa_states[closure_result]

    return dfa_start


def simulate_lexer(dfa_start, input_text):
    """
    Step 6 in pipline: Maximal Munch Simulation.
    This is the actual scanner loop that reads the source code.
    "Maximal Munch" means we don't just stop at the first valid token we see.
    Instead, we greedily follow DFA transitions as far as mathematically possible.

    If we hit a dead end (a character with no transition), we backtrack to the
    LAST known accepting state, output that token, and move our cursor to right after it.
    It also elegantly tracks line and column numbers by counting '\n' characters in the lexeme.
    """

    current_pos = 0
    line = 1
    col = 1

    # We will now use your Token class to store the results
    tokens_found = []

    print(f"{'Lexeme':<15} {'Token':<15} {'Position'}")

    while current_pos < len(input_text):
        start_pos = current_pos
        start_line = line
        start_col = col

        current_state = dfa_start
        last_accepting_pos = -1
        last_accepting_token = None

        # 1. Traverse as far as possible (Maximal Munch)
        i = current_pos
        while i < len(input_text):
            char = input_text[i]

            if char in current_state.transitions:
                current_state = current_state.transitions[char]
                if current_state.is_accepting:
                    last_accepting_pos = i
                    last_accepting_token = current_state.token_name
                i += 1
            else:
                break

        # 2. Check if we found a valid token
        if last_accepting_pos != -1:
            lexeme = input_text[start_pos : last_accepting_pos + 1]

            # Print output and create Token object (ignore spaces)
            if last_accepting_token != "SPACE":
                print(
                    f"{repr(lexeme):<15} {last_accepting_token:<15} Line {start_line}, col {start_col}"
                )
                tokens_found.append(
                    Token(last_accepting_token, lexeme, start_line, start_col)
                )

            # Update line and column trackers for the next token
            for char in lexeme:
                if char == "\n":
                    line += 1
                    col = 1
                else:
                    col += 1

            current_pos = last_accepting_pos + 1

        else:
            # 3. Lexing Error
            error_char = input_text[current_pos]
            print(
                f"\nLexing Error: Unrecognized character {repr(error_char)} at Line {line}, col {col}"
            )
            return tokens_found

    # 4. Success Message
    print("\nLexing Completed")
    return tokens_found


def run_lexical_analyzer(token_specs, input_text):
    """
    This ties the entire pipeline together. It takes the raw list of token specifications
    and the source code, and sequentially pushes data through the phases:
    1. Assigns priority based on list order.
    2. Builds individual token NFAs from regex.
    3. Combines them into a global NFA.
    4. Converts the global NFA into a DFA.
    5. Runs the Maximal Munch simulator to print the final tokens.
    """

    # 1. Create TokenRule objects automatically assigning priority based on list order
    token_rules = []
    for priority, (name, regex) in enumerate(token_specs):
        token_rules.append(TokenRule(name, regex, priority))

    # 2. Build the Global NFA
    nfa_metadata_list = []
    for rule in token_rules:
        tokens = tokenize_regex(rule.regex)
        tokens_with_concat = insert_concatenation(tokens)
        postfix = infix_to_postfix(tokens_with_concat)
        nfa_start, nfa_end = build_nfa(postfix)
        nfa_metadata_list.append((nfa_start, nfa_end, rule.name, rule.priority))

    global_nfa_start = combine_nfas(nfa_metadata_list)

    # 3. Convert to DFA
    dfa_start = build_dfa(global_nfa_start)

    # 4. Run the Lexer
    simulate_lexer(dfa_start, input_text)


if __name__ == "__main__":
    # Your token list
    # The COMPLETE token specifications list based on your project requirements
    token_specs = [
        # 1. Spaces (Now handles spaces, tabs, and actual newlines)
        ("SPACE", "( |\n|\t)+"),
        # 2. Keywords
        ("KW_IF", "if"),
        ("KW_THEN", "then"),
        ("KW_ELSE", "else"),
        ("KW_WHILE", "while"),
        ("KW_RETURN", "return"),
        ("KW_FOR", "for"),
        ("KW_BREAK", "break"),
        ("KW_CONTINUE", "continue"),
        ("KW_INT", "int"),
        ("KW_FLOAT", "float"),
        # 3. Identifiers and Numbers
        ("ID", "([A-Z]|[a-z])(([A-Z]|[a-z])|([0-9]|_))*"),
        ("NUM", r"[0-9]+(\.[0-9]+)?"),
        # 4. Operators (Longest match wins! e.g., == beats =)
        ("EQ", "=="),
        ("NEQ", "!="),
        ("LTE", "<="),
        ("GTE", ">="),
        ("ASSIGN", "="),
        ("LT", "<"),
        ("GT", ">"),
        ("OP_PLUS", r"\+"),  # Escaped because + is a regex operator
        ("OP_MINUS", r"\-"),
        ("OP_MULT", r"\*"),  # Escaped because * is a regex operator
        ("OP_DIV", "/"),
        # 5. Delimiters
        ("LPAREN", r"\("),  # Escaped because ( is a regex operator
        ("RPAREN", r"\)"),  # Escaped because ) is a regex operator
        ("LBRACE", "{"),
        ("RBRACE", "}"),
        ("SEMI", ";"),
        ("COMMA", ","),
    ]
    # Mode 1: File Input
    # If you run: python lexical_analyzer.py my_code.txt
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, "r") as file:
                input_program = file.read()
            print(f"--- Lexing File: {filename} ---\n")
            run_lexical_analyzer(token_specs, input_program)
        except FileNotFoundError:
            print(f"Error: Could not find file '{filename}'")

    # Mode 2: Interactive Scanner (REPL)
    # If you just run: python lexical_analyzer.py
    # Mode 2: Interactive Scanner (Multi-line REPL)
    else:
        print("--- Interactive Lexical Analyzer ---")
        print("Enter your code below. You can use multiple lines.")
        print("Type 'END' on a new line to process the code, or 'EXIT' to quit.\n")

        while True:
            lines = []
            try:
                # 1. Get the first line
                first_line = input("lex> ")

                if first_line.strip().upper() == "EXIT":
                    break

                # 2. Keep accumulating lines if the first line isn't END
                if first_line.strip().upper() != "END":
                    lines.append(first_line)
                    while True:
                        # Use a different prompt symbol to show we are continuing
                        line = input("...  ")
                        if line.strip().upper() == "END":
                            break
                        lines.append(line)

                # 3. Join everything into a single string with real newline characters
                input_program = "\n".join(lines)

                if input_program.strip() == "":
                    continue

                # 4. Run the lexer on the complete multi-line string
                run_lexical_analyzer(token_specs, input_program)
                print()

            except KeyboardInterrupt:
                # Handles Ctrl+C gracefully
                print("\nExiting...")
                break
            except EOFError:
                # Handles Ctrl+D / Ctrl+Z gracefully
                print("\nExiting...")
                break
