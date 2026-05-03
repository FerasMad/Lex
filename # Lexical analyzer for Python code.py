# Lexical analyzer for Python code


class TokenRule:
    def __init__(self, name, regex, priority):
        self.name = name
        self.regex = regex
        self.priority = priority


class Token:
    def __init__(self, type_name ,value, line, column):
        self.type = type_name
        self.value = value
        self.line = line
        self.column = column


class State:
    def __init__(self, is_accepting = False):
        self.is_accepting = is_accepting
        self.transitions = {}


    def add_transition(self, character, next_state):
        if character not in self.transitions:
            self.transitions[character] = []
        self.transitions[character].append(next_state)
    

def create_base_nfa(charset):
    start_state = State()
    end_state = State(is_accepting=True)
    for character in charset:
        start_state.add_transition(character, end_state)

    return (start_state, end_state)


def concatenate_nfas(nfa1, nfa2):
    nfa1_start, nfa1_end = nfa1
    nfa2_start, nfa2_end = nfa2
    nfa1_end.add_transition('epsilon', nfa2_start)
    nfa1_end.is_accepting = False
    return (nfa1_start, nfa2_end)


def union_nfas(nfa1, nfa2):
    nfa1_start, nfa1_end = nfa1
    nfa2_start, nfa2_end = nfa2
    new_start = State()
    new_end = State(is_accepting=True)
    new_start.add_transition('epsilon', nfa1_start)
    new_start.add_transition('epsilon', nfa2_start)
    nfa1_end.add_transition('epsilon', new_end)
    nfa2_end.add_transition('epsilon', new_end)
    nfa1_end.is_accepting = False
    nfa2_end.is_accepting = False
    return (new_start, new_end)


def kleene_star_nfa(nfa):
    nfa_start, nfa_end = nfa
    new_start = State()
    new_end = State(is_accepting=True)  
    new_start.add_transition('epsilon', new_end)
    new_start.add_transition('epsilon', nfa_start)
    nfa_end.add_transition('epsilon', nfa_start)
    nfa_end.add_transition('epsilon', new_end)
    nfa_end.is_accepting = False
    return (new_start, new_end)

def plus_nfa(nfa):
   return concatenate_nfas(nfa, kleene_star_nfa(nfa))


def optional_nfa(nfa):
    epsilon_nfa = create_base_nfa(['epsilon'])
    return union_nfas(nfa, epsilon_nfa)

