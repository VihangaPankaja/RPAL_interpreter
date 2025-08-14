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

def deep_copy_ast(node):
    """
    Create a deep copy of an AST node and all its children.
    
    Args:
        node: The root node of the AST to copy
        
    Returns:
        A new AST with the same structure as the original
    """
    if node is None:
        return None
        
    # Create a new node with the same label
    new_node = ASTNode(node.label)
    
    # Recursively copy all children
    new_node.children = [deep_copy_ast(child) for child in node.children]
    
    return new_node