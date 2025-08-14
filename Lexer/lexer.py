import re
from enum import Enum

# --- ENUM DEFINITION ---
class TokenType(Enum):
    KEYWORD = 1
    IDENTIFIER = 2
    INTEGER = 3
    STRING = 4
    OPERATOR = 5
    PUNCTUATION = 6
    END_OF_TOKENS = 7

# --- TOKEN CLASS ---
class MyToken:
    def __init__(self, token_type, value):
        if not isinstance(token_type, TokenType):
            raise ValueError("Token_Type not recgnized")
        self.type = token_type
        self.value = value

    def get_type(self):
        return self.type

    def get_value(self):
        return self.value

    def __repr__(self):
        return f"{self.type.name}: {self.value}"

# --- LEXER LOGIC ---
# token_specification = [
#     ('COMMENT',      r'//.*'),  # Skip comments
#     ('SPACES',       r'[ \t\n]+'),  # Skip whitespace
#     ('KEYWORD',      r'\b(let|in|fn|where|aug|or|not|gr|ge|ls|le|eq|ne|true|false|nil|dummy|within|and|rec)\b'),
#     ('STRING',       r'\'(?:\\\'|[^\'])*\''),  # String with escaped quotes
#     ('IDENTIFIER',   r'[a-zA-Z][a-zA-Z0-9_]*'),
#     ('INTEGER',      r'\d+'),
#     ('OPERATOR',     r'[+\-*<>&.@/:=~|$\#!%^_\[\]{}"\'?]+'),
#     ('PUNCTUATION',  r'[();,]')
# ]

token_specification = [
    ('COMMENT',      r'//.*'),  # Skip comments
    ('SPACES',       r'[ \t\n]+'),  # Skip whitespace
    ('KEYWORD',      r'\b(let|in|fn|where|aug|or|not|gr|ge|ls|le|eq|ne|true|false|nil|dummy|within|and|rec)\b'),
    ('STRING',       r'\'(?:\\\'|[^\'])*\''),  # String with escaped quotes
    ('IDENTIFIER',   r'[a-zA-Z][a-zA-Z0-9_]*'),
    ('INTEGER',      r'\d+'),
    # FIX: Specific multi-character operators first, then single characters
    ('OPERATOR',     r'->|>=|<=|\*\*|[+\-*<>&.@/:=~|$\#!%^_\[\]{}"?]'),  # Removed + at end, added specific multi-char ops
    ('PUNCTUATION',  r'[();,]')
]

# Compile master pattern
master_pattern = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification))

def tokenize(code: str):
    tokens = []
    for mo in master_pattern.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        
        if kind in ('SPACES', 'COMMENT'):
            continue  # Skip ignored tokens
        
        if kind not in TokenType.__members__:
            raise ValueError(f"Unknown token kind: {kind}")
        
        token_type = TokenType[kind]
        tokens.append(MyToken(token_type, value))
    
    tokens.append(MyToken(TokenType.END_OF_TOKENS, '$'))
    return tokens


