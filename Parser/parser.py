from Lexer.lexer import tokenize, MyToken, TokenType
from utils.node import ASTNode 
from enum import Enum

class ASTNode:
    def __init__(self, label, children=None):
        self.label = label
        self.children = children or []
    
    def __repr__(self):
        return f"<{self.label}>"

    def print_ast(self, level=0):
        print('.' * level + self.label)
        for child in self.children:
            child.print_ast(level + 1)

# class TokenType(Enum):
#     KEYWORD = 1
#     IDENTIFIER = 2
#     INTEGER = 3
#     STRING = 4
#     OPERATOR = 5
#     PUNCTUATION = 6
#     END_OF_TOKENS = 7

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek_token(self, offset=1):
        target_pos = self.pos + offset
        return self.tokens[target_pos] if target_pos < len(self.tokens) else None

    def match(self, expected_type=None, expected_value=None):
        token = self.current_token()
        if token and ((expected_type is None or token.type == expected_type) and
                      (expected_value is None or token.value == expected_value)):
            self.pos += 1
            return token
        raise SyntaxError(f"Unexpected token: {token}, expected {expected_value or expected_type}")

    def parse(self):
        return self.parse_expr()

    '''
    # Expressions ############################################
        E   -> `let` D `in` E => `let`
            -> `fn` Vb+ `.` E => `lambda`
            -> Ew;
        Ew  -> T `where` Dr => `where`
            -> T;
    '''
    def parse_expr(self):
        token = self.current_token()
        if token.type == TokenType.KEYWORD and token.value == 'let':
            self.match(TokenType.KEYWORD, 'let')
            d_node = self.parse_definition()
            self.match(TokenType.KEYWORD, 'in')
            e_node = self.parse_expr()
            return ASTNode('let', [d_node, e_node])
        elif token.type == TokenType.KEYWORD and token.value == 'fn':
            self.match(TokenType.KEYWORD, 'fn')
            vbs = []
            # Parse one or more Vb
            while True:
                vbs.append(self.parse_var_binding())
                next_token = self.current_token()
                if next_token and next_token.value == '.':
                    break
            # FIX: Try both PUNCTUATION and OPERATOR for '.'
            if self.current_token() and self.current_token().value == '.':
                if self.current_token().type == TokenType.PUNCTUATION:
                    self.match(TokenType.PUNCTUATION, '.')
                else:
                    self.match(TokenType.OPERATOR, '.')
            else:
                raise SyntaxError(f"Expected '.' after function parameters")
            e_node = self.parse_expr()
            return ASTNode('lambda', vbs + [e_node])
        else:
            return self.parse_expr_where()

    def parse_expr_where(self):
        t_node = self.parse_tuple()
        token = self.current_token()
        if token and token.type == TokenType.KEYWORD and token.value == 'where':
            self.match(TokenType.KEYWORD, 'where')
            dr_node = self.parse_def_rec()
            return ASTNode('where', [t_node, dr_node])
        return t_node

    '''
    # Tuple Expressions ######################################
        T   -> Ta ( ',' Ta )+ => 'tau'
            -> Ta;
        Ta  -> Ta 'aug' Tc => 'aug'
            -> Tc;
    '''
    def parse_tuple(self):
        ta_node = self.parse_tuple_aug()
        # Check if there's a comma, indicating a tuple
        if self.current_token() and self.current_token().value == ',':
            tas = [ta_node]
            while self.current_token() and self.current_token().value == ',':
                self.match(TokenType.PUNCTUATION, ',')
                tas.append(self.parse_tuple_aug())
            return ASTNode('tau', tas)
        return ta_node

    def parse_tuple_aug(self):
        tc_node = self.parse_tuple_cond()
        while self.current_token() and self.current_token().type == TokenType.KEYWORD and self.current_token().value == 'aug':
            self.match(TokenType.KEYWORD, 'aug')
            tc_node2 = self.parse_tuple_cond()
            tc_node = ASTNode('aug', [tc_node, tc_node2])
        return tc_node

    '''
    # Tuple Expressions (continued) ##########################
        Tc  -> B '->' Tc '|' Tc => '->'
            -> B;
    '''
    def parse_tuple_cond(self):
        b_node = self.parse_boolean()
        if self.current_token() and self.current_token().value == '->':
            self.match(TokenType.OPERATOR, '->')
            tc_node1 = self.parse_tuple_cond()
            self.match(TokenType.OPERATOR, '|')
            tc_node2 = self.parse_tuple_cond()
            return ASTNode('->', [b_node, tc_node1, tc_node2])
        return b_node

    '''
    # Boolean Expressions ####################################
        B   -> B 'or' Bt => 'or'
            -> Bt;
        Bt  -> Bt '&' Bs => '&'
            -> Bs;
        Bs  -> 'not' Bp => 'not'
            -> Bp;
    '''
    def parse_boolean(self):
        bt_node = self.parse_boolean_term()
        while self.current_token() and self.current_token().type == TokenType.KEYWORD and self.current_token().value == 'or':
            self.match(TokenType.KEYWORD, 'or')
            bt_node2 = self.parse_boolean_term()
            bt_node = ASTNode('or', [bt_node, bt_node2])
        return bt_node

    def parse_boolean_term(self):
        bs_node = self.parse_boolean_small()
        while self.current_token() and self.current_token().value == '&':
            self.match(TokenType.OPERATOR, '&')
            bs_node2 = self.parse_boolean_small()
            bs_node = ASTNode('&', [bs_node, bs_node2])
        return bs_node

    def parse_boolean_small(self):
        token = self.current_token()
        if token and token.type == TokenType.KEYWORD and token.value == 'not':
            self.match(TokenType.KEYWORD, 'not')
            bp_node = self.parse_boolean_primary()
            return ASTNode('not', [bp_node])
        return self.parse_boolean_primary()

    '''
    # Boolean Expressions (continued) ########################
        Bp  -> A ('gr' | '>') A => 'gr'
            -> A ('ge' | '>=') A => 'ge'
            -> A ('ls' | '<') A => 'ls'
            -> A ('le' | '<=') A => 'le'
            -> A 'eq' A => 'eq'
            -> A 'ne' A => 'ne'
            -> A;
    '''
    def parse_boolean_primary(self):
        a_node = self.parse_arithmetic()
        token = self.current_token()
        if token:
            if token.value in ['gr', '>']:
                self.match()  # Match either 'gr' or '>'
                a_node2 = self.parse_arithmetic()
                return ASTNode('gr', [a_node, a_node2])
            elif token.value in ['ge', '>=']:
                self.match()  # Match either 'ge' or '>='
                a_node2 = self.parse_arithmetic()
                return ASTNode('ge', [a_node, a_node2])
            elif token.value in ['ls', '<']:
                self.match()  # Match either 'ls' or '<'
                a_node2 = self.parse_arithmetic()
                return ASTNode('ls', [a_node, a_node2])
            elif token.value in ['le', '<=']:
                self.match()  # Match either 'le' or '<='
                a_node2 = self.parse_arithmetic()
                return ASTNode('le', [a_node, a_node2])
            elif token.value == 'eq':
                self.match(TokenType.KEYWORD, 'eq')
                a_node2 = self.parse_arithmetic()
                return ASTNode('eq', [a_node, a_node2])
            elif token.value == 'ne':
                self.match(TokenType.KEYWORD, 'ne')
                a_node2 = self.parse_arithmetic()
                return ASTNode('ne', [a_node, a_node2])
        return a_node

    '''
    # Arithmetic Expressions #################################
        A   -> A '+' At => '+'
            -> A '-' At => '-'
            -> '+' At
            -> '-' At => 'neg'
            -> At;
        At  -> At '*' Af => '*'
            -> At '/' Af => '/'
            -> Af;
        Af  -> Ap '**' Af => '**'
            -> Ap;
        Ap  -> Ap '@' R => '@'
            -> R;
    '''
    def parse_arithmetic(self):
        token = self.current_token()
        if token:
            if token.value == '+':
                self.match(TokenType.OPERATOR, '+')
                at_node = self.parse_arithmetic_term()
                return at_node  # Unary plus is a no-op
            elif token.value == '-':
                self.match(TokenType.OPERATOR, '-')
                at_node = self.parse_arithmetic_term()
                return ASTNode('neg', [at_node])

        at_node = self.parse_arithmetic_term()
        while self.current_token() and self.current_token().value in ['+', '-']:
            op = self.current_token().value
            self.match(TokenType.OPERATOR, op)
            at_node2 = self.parse_arithmetic_term()
            at_node = ASTNode(op, [at_node, at_node2])
        return at_node

    def parse_arithmetic_term(self):
        af_node = self.parse_arithmetic_factor()
        while self.current_token() and self.current_token().value in ['*', '/']:
            op = self.current_token().value
            self.match(TokenType.OPERATOR, op)
            af_node2 = self.parse_arithmetic_factor()
            af_node = ASTNode(op, [af_node, af_node2])
        return af_node

    def parse_arithmetic_factor(self):
        ap_node = self.parse_arithmetic_primary()
        if self.current_token() and self.current_token().value == '**':
            self.match(TokenType.OPERATOR, '**')
            af_node = self.parse_arithmetic_factor()
            return ASTNode('**', [ap_node, af_node])
        return ap_node

    def parse_arithmetic_primary(self):
        r_node = self.parse_rator_rand()
        while self.current_token() and self.current_token().value == '@':
            self.match(TokenType.OPERATOR, '@')
            # Check for identifier as required by grammar
            id_token = self.current_token()
            if id_token and id_token.type == TokenType.IDENTIFIER:
                self.match(TokenType.IDENTIFIER)
                id_node = ASTNode(f"<ID:{id_token.value}>")
                r_node2 = self.parse_rator_rand()
                r_node = ASTNode('@', [r_node, id_node, r_node2])
            else:
                raise SyntaxError(f"Expected identifier after @ operator, got: {id_token}")
        return r_node

    '''
    # Rators And Rands #######################################
        R   -> R Rn => 'gamma'
            -> Rn;
        Rn  -> <identifier>
            -> <integer>
            -> <string>
            -> 'true' => 'true'
            -> 'false' => 'false'
            -> 'nil' => 'nil'
            -> '(' E ')'
            -> 'dummy' => 'dummy';
    '''
    def parse_rator_rand(self):
        rn_node = self.parse_rand()
        while True:
            # Look ahead to see if there's a potential rand next
            next_token = self.current_token()
            if not next_token:
                break
            
            # If the next token could start a rand, create a gamma node
            if (next_token.type in [TokenType.IDENTIFIER, TokenType.INTEGER, TokenType.STRING] or
                (next_token.type == TokenType.KEYWORD and next_token.value in ['true', 'false', 'nil', 'dummy']) or
                (next_token.type == TokenType.PUNCTUATION and next_token.value == '(')):
                rn_node2 = self.parse_rand()
                rn_node = ASTNode('gamma', [rn_node, rn_node2])
            else:
                break
                
        return rn_node

    def parse_rand(self):
        token = self.current_token()
        if not token:
            raise SyntaxError("Unexpected end of input in rand")

        if token.type == TokenType.IDENTIFIER:
            self.match(TokenType.IDENTIFIER)
            return ASTNode(f"<ID:{token.value}>")
        elif token.type == TokenType.INTEGER:
            self.match(TokenType.INTEGER)
            return ASTNode(f"<INT:{token.value}>")
        elif token.type == TokenType.STRING:
            self.match(TokenType.STRING)
            return ASTNode(f"<STR:{token.value}>")
        elif token.type == TokenType.KEYWORD:
            if token.value == 'true':
                self.match(TokenType.KEYWORD, 'true')
                return ASTNode('true')
            elif token.value == 'false':
                self.match(TokenType.KEYWORD, 'false')
                return ASTNode('false')
            elif token.value == 'nil':
                self.match(TokenType.KEYWORD, 'nil')
                return ASTNode('<nil>')
            elif token.value == 'dummy':
                self.match(TokenType.KEYWORD, 'dummy')
                return ASTNode('dummy')
        elif token.type == TokenType.PUNCTUATION and token.value == '(':
            self.match(TokenType.PUNCTUATION, '(')
            e_node = self.parse_expr()
            self.match(TokenType.PUNCTUATION, ')')
            return e_node

        raise SyntaxError(f"Unexpected token in rand: {token}")

    '''
    # Definitions ##########################################
        D   -> Da 'within' D => 'within'
            -> Da;
        Da  -> Dr ('and' Dr)+ => 'and'
            -> Dr;
        Dr  -> 'rec' Db => 'rec'
            -> Db;
        Db  -> Vl '=' E => '='
            -> <identifier> Vb+ '=' E => 'fcn_form'
            -> '(' D ')';
    '''
    def parse_definition(self):
        da_node = self.parse_def_and()
        token = self.current_token()
        if token and token.type == TokenType.KEYWORD and token.value == 'within':
            self.match(TokenType.KEYWORD, 'within')
            d_node = self.parse_definition()
            return ASTNode('within', [da_node, d_node])
        return da_node

    def parse_def_and(self):
        dr_node = self.parse_def_rec()
        if self.current_token() and self.current_token().type == TokenType.KEYWORD and self.current_token().value == 'and':
            drs = [dr_node]
            while self.current_token() and self.current_token().type == TokenType.KEYWORD and self.current_token().value == 'and':
                self.match(TokenType.KEYWORD, 'and')
                drs.append(self.parse_def_rec())
            return ASTNode('and', drs)
        return dr_node

    def parse_def_rec(self):
        token = self.current_token()
        if token and token.type == TokenType.KEYWORD and token.value == 'rec':
            self.match(TokenType.KEYWORD, 'rec')
            db_node = self.parse_def_binding()
            return ASTNode('rec', [db_node])
        return self.parse_def_binding()

    def parse_def_binding(self):
        token = self.current_token()
        
        # Check for '(' D ')'
        if token and token.type == TokenType.PUNCTUATION and token.value == '(':
            self.match(TokenType.PUNCTUATION, '(')
            d_node = self.parse_definition()
            self.match(TokenType.PUNCTUATION, ')')
            return d_node
            
        # Check for function form: <identifier> Vb+ '=' E
        if token and token.type == TokenType.IDENTIFIER:
            # Look ahead to see if this might be a function form
            peek_token = self.peek_token()
            if (peek_token and 
                ((peek_token.type == TokenType.IDENTIFIER) or
                 (peek_token.type == TokenType.PUNCTUATION and peek_token.value == '('))):
                # This is likely a function form
                id_token = self.match(TokenType.IDENTIFIER)
                vbs = []
                
                # Parse one or more Vb
                while True:
                    next_token = self.current_token()
                    if not next_token or (next_token.value == '=' and next_token.type == TokenType.OPERATOR):
                        break
                    vbs.append(self.parse_var_binding())
                
                self.match(TokenType.OPERATOR, '=')
                e_node = self.parse_expr()
                return ASTNode('function_form', [ASTNode(f"<ID:{id_token.value}>")] + vbs + [e_node])
        
        # Otherwise, it's a simple binding: Vl '=' E
        vl_node = self.parse_var_list()
        self.match(TokenType.OPERATOR, '=')
        e_node = self.parse_expr()
        return ASTNode('=', [vl_node, e_node])

    '''
    # Variables ##############################################
        Vb  -> <identifier>
            -> '(' Vl ')'
            -> '(' ')' => '()';
        Vl  -> <identifier> list ',' => ','?;
    '''
    def parse_var_binding(self):
        token = self.current_token()
        if token.type == TokenType.IDENTIFIER:
            self.match(TokenType.IDENTIFIER)
            return ASTNode(f"<ID:{token.value}>")
        elif token.type == TokenType.PUNCTUATION and token.value == '(':
            self.match(TokenType.PUNCTUATION, '(')
            next_token = self.current_token()
            
            # Handle empty tuple '()'
            if next_token and next_token.type == TokenType.PUNCTUATION and next_token.value == ')':
                self.match(TokenType.PUNCTUATION, ')')
                return ASTNode('()')
                
            # Handle '(' Vl ')'
            vl_node = self.parse_var_list()
            self.match(TokenType.PUNCTUATION, ')')
            return vl_node
            
        raise SyntaxError(f"Unexpected token in variable binding: {token}")

    def parse_var_list(self):
        ids = []
        token = self.current_token()
        
        if token.type != TokenType.IDENTIFIER:
            raise SyntaxError(f"Expected identifier in variable list, got: {token}")
            
        ids.append(ASTNode(f"<ID:{token.value}>"))
        self.match(TokenType.IDENTIFIER)
        
        # Parse comma-separated list of identifiers
        while self.current_token() and self.current_token().type == TokenType.PUNCTUATION and self.current_token().value == ',':
            self.match(TokenType.PUNCTUATION, ',')
            token = self.current_token()
            if token.type != TokenType.IDENTIFIER:
                raise SyntaxError(f"Expected identifier after comma in variable list, got: {token}")
            ids.append(ASTNode(f"<ID:{token.value}>"))
            self.match(TokenType.IDENTIFIER)
            
        # If there's more than one ID, create a comma node
        if len(ids) > 1:
            return ASTNode(',', ids)
        return ids[0]  # Just return the single ID node