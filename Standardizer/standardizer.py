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

def standardize(node: ASTNode) -> ASTNode:
    """
    Complete standardization function for RPAL AST based on the pictorial grammar.
    Transforms syntactic sugar into standard forms using lambda calculus primitives.
    """
    label = node.label
    children = node.children
    
    # Terminal nodes (IDs, INTs, STRs) - no transformation needed
    if not children:
        return ASTNode(label)
    
    def std(child):
        """Helper to recursively standardize child nodes"""
        return standardize(child)
    
    # let X = E1 in E2 => gamma(lambda X. E2, E1)
    if label == "let":
        binding = std(children[0])  # = X E1
        e2 = std(children[1])       # E2
        x = binding.children[0]     # X
        e1 = binding.children[1]    # E1
        lam = ASTNode("lambda", [x, e2])
        return ASTNode("gamma", [lam, e1])
    
    # where E1 where X = E2 => gamma(lambda X. E1, E2)
    elif label == "where":
        e1 = std(children[0])       # E1
        binding = std(children[1])  # = X E2
        x = binding.children[0]     # X
        e2 = binding.children[1]    # E2
        lam = ASTNode("lambda", [x, e1])
        return ASTNode("gamma", [lam, e2])
    
    # function_form P V+ E => = P lambda(V+, E)
    # where P is function name, V+ are parameters, E is body
    elif label == "function_form":
        p = std(children[0])        # Function name
        params = children[1:-1]     # Parameters V+
        e = std(children[-1])       # Body E
        
        # Create nested lambdas for multiple parameters
        lambda_expr = e
        for param in reversed(params):
            lambda_expr = ASTNode("lambda", [std(param), lambda_expr])
        
        return ASTNode("=", [p, lambda_expr])
    
    # lambda V+ E => nested lambdas lambda(V1, lambda(V2, ...lambda(Vn, E)))
    elif label == "lambda":
        params = children[:-1]      # Parameters V+
        body = std(children[-1])    # Body E
        
        # Create nested lambdas from right to left
        result = body
        for param in reversed(params):
            result = ASTNode("lambda", [std(param), result])
        return result
    
    # rec X = E => = X gamma(Y*, lambda X. E)
    elif label == "rec":
        binding = std(children[0])  # = X E
        x = binding.children[0]     # X
        e = binding.children[1]     # E
        lam = ASTNode("lambda", [x, e])
        ystar = ASTNode("<Y*>", [])
        gamma_node = ASTNode("gamma", [ystar, lam])
        return ASTNode("=", [x, gamma_node])
    
    # within (X1 = E1) within (X2 = E2) => = X1 gamma(lambda X2. E2, E1)
    # elif label == "within":
    #     bind1 = std(children[0])    # = X1 E1
    #     bind2 = std(children[1])    # = X2 E2
    #     x1 = bind1.children[0]      # X1
    #     e1 = bind1.children[1]      # E1
    #     x2 = bind2.children[0]      # X2
    #     e2 = bind2.children[1]      # E2
    #     lam = ASTNode("lambda", [x2, e2])
    #     gamma_node = ASTNode("gamma", [lam, e1])
    #     return ASTNode("=", [x1, gamma_node])
    
    elif label == "within":
        bind1 = std(children[0])  # = c 3
        bind2 = std(children[1])  # = f λx.(x + c)
        x1 = bind1.children[0]
        e1 = bind1.children[1]
        x2 = bind2.children[0]
        e2 = bind2.children[1]
        # Correct: apply (λx1. e2) to e1
        lam = ASTNode("lambda", [x1, e2])
        gamma_node = ASTNode("gamma", [lam, e1])
        # x2 = (λx1. e2)(e1)
        return ASTNode("=", [x2, gamma_node])


    # and (X1 = E1, X2 = E2, ...) => = tau(X1, X2, ...) tau(E1, E2, ...)
    elif label == "and":
        ids = []
        exprs = []
        for binding in children:
            std_bind = std(binding)  # = Xi Ei
            ids.append(std_bind.children[0])    # Xi
            exprs.append(std_bind.children[1])  # Ei
        
        tau_ids = ASTNode("tau", ids)
        tau_exprs = ASTNode("tau", exprs)
        return ASTNode("=", [tau_ids, tau_exprs])
    
    # tau E+ => tau(E+) (keep tau as-is, just standardize children)
    elif label == "tau":
        return ASTNode("tau", [std(child) for child in children])
    
    # -> B T E => gamma(gamma(gamma(->, B), T), E)
    elif label == "->":
        b = std(children[0])    # Boolean condition
        t = std(children[1])    # Then expression
        e = std(children[2])    # Else expression
        arrow_op = ASTNode("->", [])
        
        return ASTNode("gamma", [
            ASTNode("gamma", [
                ASTNode("gamma", [arrow_op, b]),
                t
            ]),
            e
        ])
    
    # @ E1 N E2 => gamma(gamma(E1, N), E2)

    elif label == "@":
        e1 = std(children[0])   # Tuple/structure
        n = std(children[1])    # Index
        e2 = std(children[2])   # Context expression
        
        return ASTNode("gamma", [
            ASTNode("gamma", [n, e1]),
            e2
        ])
    
    # Binary operators that should remain as direct binary operations
    # These are NOT converted to curried gamma form in the original RPAL
    elif label in {"&", "or", "eq", "ne", "gr", "ge", "ls", "le"}:
        return ASTNode(label, [std(children[0]), std(children[1])])
    
    # Binary operators that ARE converted to curried gamma form
    elif label in {"aug", "+", "-", "*", "/", "**"}:
        e1 = std(children[0])
        e2 = std(children[1])
        op_node = ASTNode(label, [])
        
        return ASTNode("gamma", [
            ASTNode("gamma", [op_node, e1]),
            e2
        ])
    
    # Unary operators: not, neg
    # Uop E => gamma(Uop, E)
    elif label in {"not", "neg"}:
        e = std(children[0])
        op_node = ASTNode(label, [])
        return ASTNode("gamma", [op_node, e])
    
    # fcn_form alternative: P V+ . E => = P lambda(V+, E)
    # This handles the case where function parameters are followed by a dot
    elif label == "fcn_form" and len(children) >= 3:
        p = std(children[0])        # Function name
        # Check if there's a dot separator
        dot_index = -1
        for i, child in enumerate(children[1:], 1):
            if child.label == ".":
                dot_index = i
                break
        
        if dot_index > 0:
            params = children[1:dot_index]      # Parameters before dot
            body = std(children[dot_index+1])   # Expression after dot
        else:
            params = children[1:-1]             # All but first and last
            body = std(children[-1])            # Last child is body
        
        # Create nested lambdas
        lambda_expr = body
        for param in reversed(params):
            lambda_expr = ASTNode("lambda", [std(param), lambda_expr])
        
        return ASTNode("=", [p, lambda_expr])
    
    # Assignment: = X E => = X E (already in standard form, just standardize children)
    elif label == "=":
        return ASTNode("=", [std(children[0]), std(children[1])])
    
    # Application: gamma E1 E2 => gamma E1 E2 (standardize children)
    elif label == "gamma":
        return ASTNode("gamma", [std(children[0]), std(children[1])])
    
    # Conditional expressions might have special handling
    elif label == "Cond":
        # Cond B T E => -> B T E
        if len(children) == 3:
            b = std(children[0])
            t = std(children[1])
            e = std(children[2])
            return standardize(ASTNode("->", [b, t, e]))
        else:
            return ASTNode(label, [std(child) for child in children])
    
    # Default case: recursively standardize all children
    else:
        return ASTNode(label, [std(child) for child in children])
