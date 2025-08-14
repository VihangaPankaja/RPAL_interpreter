import sys
from utils.file_io import read_source_file
from Lexer.lexer import tokenize
from Parser.parser import Parser
from Standardizer.standardizer import standardize
from utils.node import deep_copy_ast
from flattener.flat import STFlattener, OptimizedFlattener
from CSE_Machine.cse_machine import CSEMachineExecutor

def print_help():
    help_text = """
Usage: python myrpal.py <file_name> [options]

Options:
  -h, --help       Show this help message
  -ast             Print the original Abstract Syntax Tree (AST)
  -st              Print the standardized tree (after standardization)
  -flat            Print the standard flattened control structure
  -optflat         Print the optimized flattened control structure
  -cse             Print the execution trace from the CSE machine
  -allt            Print both AST and standardized tree

Testing: To run sample test cases and get results, use the following command:
  python test_rpal.py
  """
    print(help_text)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        return

    file_name = sys.argv[1]
    flags = sys.argv[2:]  # All optional flags

    # Step 1: Read and tokenize
    source_code = read_source_file(file_name)
    tokens = tokenize(source_code)

    # Step 2: Parse and standardize
    parser = Parser(tokens)
    ast = parser.parse()
    ast_copy = deep_copy_ast(ast)
    standardized_tree = standardize(ast_copy)

    # Step 3: Flatten and optimize
    flattener = STFlattener()
    controls = flattener.flatten(standardized_tree)

    opt_flattener = OptimizedFlattener()
    optimized_controls = opt_flattener.flatten(standardized_tree)

    # Step 4: Optional visualizations
    if "-ast" in flags:
        #print("Abstract Syntax Tree:")
        ast.print_ast()
    if "-st" in flags:
        print("\nStandardized Tree:")
        standardized_tree.print_ast()
    if "-flat" in flags:
        print("\nStandard Flattened Control Structure:")
        for control_id, control in controls.items():
            print(f"Control {control_id}: {control}")
    if "-optflat" in flags:
        print("\nOptimized Flattened Control Structure:")
        for control_id, control in optimized_controls.items():
            print(f"Control {control_id}: {control}")
    if "-allt" in flags:
        print("\nAST:")
        ast.print_ast()
        print("\nStandardized Tree:")
        standardized_tree.print_ast()

    # Step 5: Run CSE machine
    cse = CSEMachineExecutor(optimized_controls)
    result = cse.run()
    if "-cse" in flags:
        print("\nCSE Machine Execution Trace:")
        cse.print_trace()
    # elif not flags:
    #     print("Program Output:", result)
    # print(result)
if __name__ == "__main__":
    main()
