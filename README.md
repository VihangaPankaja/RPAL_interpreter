# RPAL Interpreter

A functional programming language interpreter implementation of RPAL (Right-reference Pedagogical Algorithmic Language) built in Python.

## 🚀 Features

- **Lexical Analysis**: Tokenizes RPAL source code
- **Syntax Parsing**: Builds Abstract Syntax Trees (AST)
- **Tree Standardization**: Converts AST to standardized form
- **Control Structure Flattening**: Two-level flattening with optimization
- **CSE Machine Execution**: Executes flattened control structures
- **Debug Visualization**: Multiple output modes for debugging and learning

## 📋 Requirements

- Python 3.6+
- No external dependencies required

## 🛠️ Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd rpal-interpreter
```

2. Ensure all modules are in place:

```
├── myrpal.py
├── utils/
│   ├── file_io.py
│   └── node.py
├── Lexer/
│   └── lexer.py
├── Parser/
│   └── parser.py
├── Standardizer/
│   └── standardizer.py
├── flattener/
│   └── flat.py
└── CSE_Machine/
    └── cse_machine.py
```

## 🎯 Usage

### Basic Usage

```bash
python myrpal.py <filename.rpal>
```

### Available Options

| Flag         | Description                                     |
| ------------ | ----------------------------------------------- |
| `-h, --help` | Show help message                               |
| `-ast`       | Print the original Abstract Syntax Tree         |
| `-st`        | Print the standardized tree                     |
| `-flat`      | Print the standard flattened control structure  |
| `-optflat`   | Print the optimized flattened control structure |
| `-cse`       | Print the CSE machine execution trace           |
| `-allt`      | Print both AST and standardized tree            |

### Examples

```bash
# Run a simple RPAL program
python myrpal.py example.rpal

# View the Abstract Syntax Tree
python myrpal.py example.rpal -ast

# View execution trace
python myrpal.py example.rpal -cse

# View all tree representations
python myrpal.py example.rpal -allt

# View optimized flattening
python myrpal.py example.rpal -optflat

# To run Sample test cases
python test_rpal.py
```

✅ How to Use This Makefile

```bash
make run file=test.rpal     # Run the program normally
make ast file=test.rpal     # Print AST only
make st file=test.rpal      # Print Standardized Tree
make flat file=test.rpal    # Print unoptimized flattened structure
make optflat file=test.rpal # Print optimized flattened structure
make cse file=test.rpal     # Execute using CSE machine with trace
make allt file=test.rpal    # Print AST and ST
make clean                  # Clean cache and pyc files
```

## 📝 Sample RPAL Code

```rpal
let rec factorial n =
    if (eq n 0) then 1
    else (mult n (factorial (sub n 1)))
in factorial 5
```

## 🏗️ Architecture

The interpreter follows a multi-stage compilation pipeline:

1. **Lexical Analysis** - Converts source code into tokens
2. **Parsing** - Builds Abstract Syntax Tree from tokens
3. **Standardization** - Transforms AST into standardized form
4. **Flattening** - Converts to control structures (standard + optimized)
5. **Execution** - Runs code using CSE (Control Stack Environment) machine

## 🔧 Components

- **Lexer**: Tokenizes RPAL source code
- **Parser**: Builds AST using recursive descent parsing
- **Standardizer**: Applies standardization rules to AST
- **Flattener**: Two implementations (standard and optimized)
- **CSE Machine**: Stack-based execution engine
- **Utils**: File I/O and AST utilities

## 🐛 Debugging

Use the various flag options to inspect different stages of compilation:

- Start with `-ast` to verify parsing
- Use `-st` to check standardization
- Use `-flat` and `-optflat` to compare flattening strategies
- Use `-cse` to trace execution step-by-step

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🎓 Educational Purpose

This interpreter is designed for educational purposes to understand:

- Functional programming language implementation
- Compiler design principles
- Abstract syntax trees and program transformation
- Stack-based execution models

---

_Built with ❤️ for learning functional programming language implementation_
