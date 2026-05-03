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

def preprocess_regex(regex):
    result = []

    for i in range(len(regex)):
        current_char = regex[i]
        result.append(current_char)

        if i + 1 < len(regex):
            next_char = regex[i+1]
            
            left_valid = current_char not in ['(', '|']
            right_valid = next_char not in ['*', '+', '?', '|', ')']

            if right_valid and left_valid:
                result.append('.')
            
    return ''.join(result)

def infix_to_postfix(regex):
    regex = preprocess_regex(regex)

    output = []
    stack = []
    precedence = {'*' : 2, '+' : 2, '?' : 2, '.' : 1, '|' : 0}

    for char in regex:
        if char == '(':
            stack.append(char)
        elif char == ')':
            while len(stack) > 0 and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        elif char in precedence:
            while len(stack) > 0 and stack[-1] != '(' and precedence[stack[-1]] >= precedence[char]:
                output.append(stack.pop())
            stack.append(char)
        else:
            output.append(char)
        
    while len(stack) > 0:
        output.append(stack.pop())

    return ''.join(output)


def build_nfa(postfix):
    stack = []

    for char in postfix:
        if char in ['*', '+', '?']:
            nfa = stack.pop()
            if char == '*':
                stack.append(kleene_star_nfa(nfa))
            elif char == '+':
                stack.append(plus_nfa(nfa))
            elif char == '?':
                stack.append(optional_nfa(nfa))

        elif char in ['.', '|']:
            nfa2 = stack.pop()
            nfa1 = stack.pop()

            if char == '.':
                stack.append(concatenate_nfas(nfa1, nfa2))
            elif char == '|':
                stack.append(union_nfas(nfa1, nfa2))

        else:
            stack.append(create_base_nfa([char]))
    return stack.pop()


def get_epsilon_closure(states):
    closure = set(states) # Start by including the original states
    stack = list(states)  # Use a stack to explore

    # 1. While the stack has items:
    while len(stack) > 0:
        current_state = stack.pop()
        if 'epsilon' in current_state.transitions:
            for next_state in current_state.transitions['epsilon']:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)

    return closure


def evaluate(nfa, word):
    start_state, end_state = nfa
    current_states = get_epsilon_closure([start_state])

    for char in word:
        next_states = set()
    
        for state in current_states:
            if char in state.transitions:
                next_states.update(state.transitions[char])
        current_states = get_epsilon_closure(list(next_states))

    return end_state in current_states