# Lexical Analyzer

**Course:** CSC339 Theory of Computation — King Saud University, 2026  
**Team:** Feras Madkhali, Abdulmajeed Alwardi, Abdulaziz Alabdullatif  

This repository contains a Lexical Analyzer implemented entirely from scratch in Python. The program ingests a defined list of token specifications and an input source file, systematically producing a stream of recognized tokens through a rigorous Regular Expression → NFA → DFA → Simulation pipeline.

**Link to project:** [https://github.com/FerasMad/Lex](https://github.com/FerasMad/Lex)



## Implementation Journey and Methodology

**Technologies Utilized:** Python, VS Code, GitHub

The development of this Lexical Analyzer presented several significant conceptual challenges. A primary obstacle was shifting from standard runtime input processing to a structured tokenization model, where source text must be evaluated and categorized into a list of tokens for subsequent compilation phases rather than being executed. 

Through extensive research into compiler design principles, we successfully bridged the gap between theoretical automata concepts and practical software engineering. The implementation follows a strict procedural pipeline:

1. **Preprocessing & Parsing:** We utilized the Shunting Yard algorithm to convert standard infix regular expressions into postfix notation. This step included optimizing the raw regex input by dynamically expanding character classes (e.g., `[a-z]`) and injecting explicit concatenation operators.
2. **Automata Construction:** Following preprocessing, Thompson's construction algorithm was employed to systematically generate Non-Deterministic Finite Automata (NFAs) for each individual token specification.
3. **Unification and Determinization:** Rather than simulating concurrent automata, these individual NFAs were merged under a single global start state to form one comprehensive NFA. We then processed this combined graph through the subset construction algorithm. By computing $\epsilon$-closures, the algorithm elegantly absorbed all non-deterministic $\epsilon$-transitions, generating **a single, unified Deterministic Finite Automaton (DFA)**. During this conversion, accepting DFA states were pre-configured to resolve token overlap conflicts using the strict priority hierarchy defined in our specifications.
4. **Lexical Simulation:** Finally, the analyzer scans the input stream utilizing the Maximal Munch principle. The algorithm traverses the unified DFA to identify the longest valid matching sequence, correctly falls back to the last known accepting state upon reaching a dead end, and outputs the resulting token alongside its exact positional metadata.

## Core Architectural Features
By adhering to the constraint of avoiding external regular expression libraries, the underlying engine handles all automata logic natively:
* **Custom Regular Expression Engine:** Programmatically expands bracketed character classes (e.g., `[a-z]`), processes literal escape sequences (e.g., `\+`), and dynamically injects implicit concatenation operators.
* **Subset Construction & Conflict Resolution:** In instances where an input string satisfies multiple token rules (e.g., recognizing an input as both a keyword and an identifier), the DFA states are pre-configured to resolve the conflict based on strict specification hierarchy.
* **Maximal Munch Algorithm:** Implements robust forward-tracking and backtracking mechanisms to ensure accurate token boundary detection.
* **Precise Positional Tracking:** Accurately calculates line and column coordinates, successfully accounting for invisible whitespace, tabs, and newline characters during multiline input analysis.

## Execution Instructions

The lexical analyzer supports two modes of operation:

**1. Interactive Mode (Multi-line REPL)**
Execute the script without parameters to initialize the interactive prompt. This mode supports multiline input. Upon completion of your code block, type `END` on a new line to initiate the lexical analysis.
```bash
python lexical_analyzer.py
```

**2. File Execution Mode**
To analyze an existing source code file, pass the target filename as a command-line argument.
```bash
python lexical_analyzer.py source_code.txt
```

## Example Output
Given the sample input sequence: `if x > y then {x=y; z=x-1} else x=y+5`

The analyzer successfully processes the text and generates the following standardized token stream:

```text
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
'x'             ID              Line 1, col 30
'='             ASSIGN          Line 1, col 31
'y'             ID              Line 1, col 32
'+'             OP_PLUS         Line 1, col 33
'5'             NUM             Line 1, col 34

Lexing Completed
```