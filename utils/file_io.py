'''Utils.py consists of utility functions for the RPAL interpreter.'''

def read_source_file(file_path: str) -> str:
    """Reads the RPAL source code from a file and returns it as a string."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        exit(1)
