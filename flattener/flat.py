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

class STFlattener:
    """
    Flattens standardized RPAL trees into control structures for the CSE Machine.
    Works with the ASTNode structure from your standardization code.
    """
    
    def __init__(self):
        self.control_counter = 1
        self.control_structures = {}
    
    def flatten(self, st_root: ASTNode) -> dict:
        """
        Main function to flatten a standardized tree.
        Returns a dictionary of control structures indexed by their IDs.
        """
        self.control_counter = 1
        self.control_structures = {}
        
        # Generate delta_0 (main control structure)
        delta_0 = self._generate_control(st_root)
        self.control_structures[0] = delta_0
        
        return self.control_structures
    
    def _generate_control(self, node: ASTNode) -> list:
        """
        Generate control structure for a given node using pre-order traversal.
        Returns a list of control symbols.
        """
        if not node:
            return []
        
        label = node.label
        children = node.children
        control = []
        
        # Terminal nodes (identifiers, integers, strings, operators without children)
        if not children:
            if label.startswith('<') and label.endswith('>'):
                # Handle tokens like <ID:x>, <INT:5>, <STR:"hello">
                if ':' in label:
                    control.append(label.split(':')[1].rstrip('>'))
                else:
                    control.append(label.strip('<>'))
            else:
                control.append(label)
            return control
        
        # Gamma (function application)
        if label == "gamma":
            # Generate control for both operands
            rator_control = self._generate_control(children[0])  # Function
            rand_control = self._generate_control(children[1])   # Argument
            
            # Add in reverse order (argument first, then function, then gamma)
            control.extend(rand_control)
            control.extend(rator_control)
            control.append('γ')
            
        # Lambda (function definition)
        elif label == "lambda":
            if len(children) >= 2:
                param_node = children[0]
                body = children[1]
                
                lambda_id = self.control_counter
                self.control_counter += 1
                
                # Generate the delta for the lambda body
                self.control_structures[lambda_id] = self._generate_control(body)
                
                # Process parameter name(s)
                if param_node.label == ",":
                    param_names = ','.join(
                        child.label.split(':')[1].rstrip('>') if ':' in child.label else child.label
                        for child in param_node.children
                    )
                else:
                    param_names = param_node.label.split(':')[1].rstrip('>') if ':' in param_node.label else param_node.label

                control.append(f'λ{param_names}^{lambda_id}')

        
        # Assignment (not processed in control structure, but children are)
        elif label == "=":
            # For assignments, we typically only need the value part in control
            # The binding is handled by the environment
            control.extend(self._generate_control(children[1]))
        
        # Tau (tuple formation)
        elif label == "tau":
            n = len(children)
            # Process children in reverse order for stack
            for child in reversed(children):
                control.extend(self._generate_control(child))
            control.append(f'τ{n}')
        
        # Conditional arrow (->)
        elif label == "->":
            if len(children) >= 3:
                # This should be in the form: gamma(gamma(gamma(->, B), T), E)
                # We need to extract B, T, E from the nested gamma structure
                
                # For a standardized conditional, we expect:
                # gamma(gamma(gamma(->, B), T), E)
                # Extract the condition, then, and else parts
                condition, then_expr, else_expr = self._extract_conditional_parts(node)
                
                if condition and then_expr and else_expr:
                    # Generate control structures for then and else branches
                    then_id = self.control_counter
                    self.control_counter += 1
                    else_id = self.control_counter
                    self.control_counter += 1
                    
                    self.control_structures[then_id] = self._generate_control(then_expr)
                    self.control_structures[else_id] = self._generate_control(else_expr)
                    
                    # Generate control for condition
                    control.extend(self._generate_control(condition))
                    control.append('β')
                    control.append(f'δ{else_id}')
                    control.append(f'δ{then_id}')
                else:
                    # Fallback: treat as regular gamma
                    for child in reversed(children):
                        control.extend(self._generate_control(child))
                    control.append('γ')
        
        # Binary operators
        elif label in {"+", "-", "*", "/", "**", "aug", "&", "or", "eq", "ne", "gr", "ge", "ls", "le"}:
            if len(children) == 2:
                # For standardized binary ops, they should be in gamma form
                # gamma(gamma(op, E1), E2)
                # We want to generate: E1 E2 op
                right_control = self._generate_control(children[1])
                left_control = self._generate_control(children[0])
                
                control.extend(right_control)
                control.extend(left_control)
                control.append(label)
            else:
                # If not in expected form, process as gamma
                for child in reversed(children):
                    control.extend(self._generate_control(child))
                control.append('γ')
        
        # Unary operators
        elif label in {"not", "neg"}:
            if len(children) == 1:
                # For standardized unary ops: gamma(op, E)
                # We want: E op
                control.extend(self._generate_control(children[0]))
                control.append(label)
            else:
                # Fallback
                for child in reversed(children):
                    control.extend(self._generate_control(child))
                control.append('γ')
        
        # Y* combinator (for recursion)
        elif label == "<Y*>":
            control.append('Y*')
        
        # Default case: process children and add current label
        else:
            for child in reversed(children):
                control.extend(self._generate_control(child))
            
            # Add the current node's label if it's an operator
            if label not in {"program", "expression"}:  # Skip structural labels
                control.append(label)
        
        return control
    
    def _extract_conditional_parts(self, node: ASTNode):
        """
        Extract condition, then, and else parts from a standardized conditional.
        Expected form: gamma(gamma(gamma(->, B), T), E)
        """
        if (node.label == "gamma" and len(node.children) == 2 and
            node.children[0].label == "gamma" and len(node.children[0].children) == 2 and
            node.children[0].children[0].label == "gamma" and len(node.children[0].children[0].children) == 2 and
            node.children[0].children[0].children[0].label == "->"):
            
            # Extract parts
            condition = node.children[0].children[0].children[1]  # B
            then_expr = node.children[0].children[1]              # T  
            else_expr = node.children[1]                          # E
            
            return condition, then_expr, else_expr
        
        return None, None, None
    
    def print_control_structures(self, control_structures: dict):
        """
        Pretty print the control structures.
        """
        for delta_id, control in control_structures.items():
            print(f"δ{delta_id} = {' '.join(control)}")

# Example usage and testing
def test_flattener():
    """Test the flattener with some example trees"""
    
    # Test 1: Simple arithmetic - (+ 2 3)
    # Standardized form: gamma(gamma(+, 2), 3)
    print("=== Test 1: Simple arithmetic (+ 2 3) ===")
    
    plus_op = ASTNode("+", [])
    two = ASTNode("2", [])
    three = ASTNode("3", [])
    
    inner_gamma = ASTNode("gamma", [plus_op, two])
    outer_gamma = ASTNode("gamma", [inner_gamma, three])
    
    flattener = STFlattener()
    controls = flattener.flatten(outer_gamma)
    flattener.print_control_structures(controls)
    
    print("\n=== Test 2: Lambda expression (λx.x+1) 5 ===")
    
    # Lambda part: λx.(+ x 1)
    x_param = ASTNode("x", [])
    x_ref = ASTNode("x", [])
    one = ASTNode("1", [])
    plus_op2 = ASTNode("+", [])
    
    # Body: gamma(gamma(+, x), 1)
    inner_gamma2 = ASTNode("gamma", [plus_op2, x_ref])
    body_gamma = ASTNode("gamma", [inner_gamma2, one])
    
    # Lambda: lambda(x, body)
    lambda_node = ASTNode("lambda", [x_param, body_gamma])
    
    # Application: gamma(lambda, 5)
    five = ASTNode("5", [])
    app_gamma = ASTNode("gamma", [lambda_node, five])
    
    flattener2 = STFlattener()
    controls2 = flattener2.flatten(app_gamma)
    flattener2.print_control_structures(controls2)
    
    print("\n=== Test 3: Conditional (-> true 1 2) ===")
    
    # Standardized form: gamma(gamma(gamma(->, true), 1), 2)
    arrow_op = ASTNode("->", [])
    true_val = ASTNode("true", [])
    one_val = ASTNode("1", [])
    two_val = ASTNode("2", [])
    
    inner_gamma3 = ASTNode("gamma", [arrow_op, true_val])
    middle_gamma = ASTNode("gamma", [inner_gamma3, one_val])
    cond_gamma = ASTNode("gamma", [middle_gamma, two_val])
    
    flattener3 = STFlattener()
    controls3 = flattener3.flatten(cond_gamma)
    flattener3.print_control_structures(controls3)



class OptimizedFlattener:
    def __init__(self):
        self.control_counter = 1
        self.control_structures = {}

    def flatten(self, node: ASTNode) -> dict:
        self.control_counter = 1
        self.control_structures = {}
        self.control_structures[0] = self._generate_control(node)
        return self.control_structures

    def _generate_control(self, node: ASTNode) -> list:
        if not node:
            return []

        label = node.label
        children = node.children
        control = []

        # Terminal
        if not children:
            return [self._extract_terminal_value(label)]

        # Gamma
        if label == 'gamma':
            left = children[0]
            right = children[1]

            # Detect curried binary ops: gamma(gamma(op, x), y)
            if (left.label == 'gamma' and len(left.children) == 2 and
                left.children[0].label in {'+', '-', '*', '/', '**', 'eq', 'ne', 'gr', 'ge', 'ls', 'le', 'aug'}):
                op = left.children[0].label
                x = left.children[1]
                y = right
                control += self._generate_control(x)
                control += self._generate_control(y)
                control.append(op)
                return control

            # Detect unary op: gamma(neg, x)
            if left.label in {'neg', 'not'}:
                control += self._generate_control(right)
                control.append(left.label)
                return control

            # Detect conditional: gamma(gamma(gamma('->', B), T), E)
            if (left.label == 'gamma' and left.children[0].label == 'gamma' and
                left.children[0].children[0].label == '->'):
                B = left.children[0].children[1]
                T = left.children[1]
                E = right

                then_id = self.control_counter
                self.control_counter += 1
                else_id = self.control_counter
                self.control_counter += 1

                self.control_structures[then_id] = self._generate_control(T)
                self.control_structures[else_id] = self._generate_control(E)

                control += self._generate_control(B)
                control.append(f'β')  # beta
                control.append(f'δ{else_id}')
                control.append(f'δ{then_id}')
                return control

            # Standard application
            control += self._generate_control(right)
            control += self._generate_control(left)
            control.append('γ')  # gamma
            return control
        # Tuple
        elif label == 'tau':
            for child in reversed(children):  # FIXED: Don't reverse
                control += self._generate_control(child)
            control.append(f'τ{len(children)}')
            return control

        # Lambda
        elif label == 'lambda':
            param_node = children[0]
            body_node = children[1]
            lambda_id = self.control_counter
            self.control_counter += 1

            self.control_structures[lambda_id] = self._generate_control(body_node)

            if param_node.label in {',', 'tau'}:  # FIXED: support tau param lists
                vars = ','.join([self._extract_terminal_value(p.label) for p in param_node.children])
            else:
                vars = self._extract_terminal_value(param_node.label)

            control.append(f'λ{vars}^{lambda_id}')
            return control

        # # Lambda
        # elif label == 'lambda':
        #     param_node = children[0]
        #     body_node = children[1]
        #     lambda_id = self.control_counter
        #     self.control_counter += 1

        #     self.control_structures[lambda_id] = self._generate_control(body_node)

        #     if param_node.label == ',':
        #         vars = ','.join([self._extract_terminal_value(p.label) for p in param_node.children])
        #     else:
        #         vars = self._extract_terminal_value(param_node.label)

        #     control.append(f'λ{vars}^{lambda_id}')  # lambda
        #     return control

        # # Tuple
        # elif label == 'tau':
        #     for child in reversed(children):
        #         control += self._generate_control(child)
        #     control.append(f'τ{len(children)}')  # tau
        #     return control

        # Binary and Unary Ops
        elif label in {'+', '-', '*', '/', '**', 'eq', 'ne', 'gr', 'ge', 'ls', 'le', 'aug', '&', 'or'}:
            control += self._generate_control(children[0])
            control += self._generate_control(children[1])
            control.append(label)
            return control

        elif label in {'neg', 'not'}:
            control += self._generate_control(children[0])
            control.append(label)
            return control

        # Assignment
        elif label == '=':
            control += self._generate_control(children[1])
            return control

        # Default recursive case
        for child in children:
            control += self._generate_control(child)
        return control

    # def _extract_terminal_value(self, label):
    #     if label.startswith('<') and ':' in label:
    #         return label.split(':')[1].rstrip('>')
    #     return label
    def _extract_terminal_value(self, label):
        if label.startswith('<') and ':' in label:
            type_part, value_part = label[1:-1].split(':', 1)
            if type_part == 'INT':
                return int(value_part)
            else:
                return label.split(':')[1].rstrip('>')
        return label

    def print_control_structures(self):
        for delta_id, control in self.control_structures.items():
            print(f'δ{delta_id} = {" ".join(control)}')