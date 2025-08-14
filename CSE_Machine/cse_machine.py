import copy

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

class Environment:
    def __init__(self, index=0, parent=None):
        self.index = index
        self.bindings = {}
        self.parent = parent
        self.is_removed = False

    def lookup(self, var):
        if var in self.bindings:
            return self.bindings[var]
        elif self.parent:
            return self.parent.lookup(var)
        raise NameError(f"Unbound identifier: {var}")

    def extend(self, var, value):
        self.bindings[var] = value
    
    def set_removed(self, removed):
        self.is_removed = removed
    
    def get_removed(self):
        return self.is_removed

class Closure:
    def __init__(self, params, delta_id, env_index):
        self.params = params  # list of variable names
        self.delta_id = delta_id
        self.env_index = env_index  # Store environment index instead of reference

    def __repr__(self):
        return f"<Closure λ{','.join(self.params)}^{self.delta_id}>"

class Eta:
    def __init__(self, closure):
        self.closure = closure  # The original closure from Y*
        
    def __repr__(self):
        return f"<Eta {self.closure}>"

class CSEMachineExecutor:
    def __init__(self, control_structures):
        self.control_structures = control_structures
        self.stack = []
        self.environments = [Environment(0)]  # List of environments
        self.current_env = self.environments[0]  # Current active environment
        self.control = list(reversed(control_structures[0]))  # Start from δ0
        self.env_counter = 1
        self.trace_log = []
        self.builtins = {
            'Print', 'Isinteger', 'Isstring', 'Istuple', 'Isdummy',
            'Istruthvalue', 'Isfunction', 'Stem', 'Stern', 'Conc',
            'Order', 'Null', 'ItoS', 'print',
        }

    def lookup(self, var):
        return self.current_env.lookup(var)
    
    def find_env_by_index(self, index):
        for env in self.environments:
            if env.index == index:
                return env
        return None
    
    def record_state(self, instr):
        state = {
            'instr': instr,
            'control': list(reversed(self.control)),  # keep in natural order
            'stack': list(self.stack),               # shallow copy for snapshot
            'current_env': self.current_env.index,
            'active_envs': [f'e{env.index}' for env in self.environments if not env.is_removed]
        }
        self.trace_log.append(state)
    
    def print_trace(self):
        for i, state in enumerate(self.trace_log):
            print(f"\nStep {i+1}:")
            print(f"  Instruction: {state['instr']}")
            print(f"  Control: {state['control']}")
            print(f"  Stack: {state['stack']}")
            print(f"  Current Env: e{state['current_env']}")
            print(f"  Active Envs: {state['active_envs']}")


    def apply_binary(self, op, left, right):
        if op in ['+', '-', '*', '/', '**']:
            left, right = int(left), int(right)
            if op == '+':
                return int(left + right)
            elif op == '-':
                return int(left - right)
            elif op == '*':
                return int(left * right)
            elif op == '/':
                return int(left // right)
            elif op == '**':
                return int(left ** right)

        elif op in ['eq', 'ne']:
            if op == 'eq':
                return 'true' if left == right else 'false'
            elif op == 'ne':
                return 'true' if left != right else 'false'

        elif op in ['<', '>', '<=', '>=', 'ls', 'gr', 'le', 'ge']:
            # Try numeric comparison first
            try:
                left_num = int(left)
                right_num = int(right)
                left, right = left_num, right_num
                numeric = True
            except ValueError:
                # Fallback to string comparison
                numeric = False

            if op == '<' or op == 'ls':
                return 'true' if left < right else 'false'
            elif op == '>' or op == 'gr':
                return 'true' if left > right else 'false'
            elif op == '<=' or op == 'le':
                return 'true' if left <= right else 'false'
            elif op == '>=' or op == 'ge':
                return 'true' if left >= right else 'false'

        elif op in ['or', '&']:
            if op == 'or':
                return 'true' if left == 'true' or right == 'true' else 'false'
            elif op == '&':
                return 'true' if left == 'true' and right == 'true' else 'false'

        else:
            raise ValueError(f"Unknown operator: {op}")


    
    def apply_unary(self, op, operand):
        if op == 'neg':
            operand = int(operand)
            return -operand
        elif op == 'not':
            if operand == 'true':
                return 'false'
            elif operand == 'false':
                return 'true'
            else:
                raise ValueError(f"Invalid boolean value for 'not': {operand}")
        else:
            raise ValueError(f"Unknown unary operator: {op}")
    
    def format_tuple(self,tup):
        parts = []
        for item in tup:
            if isinstance(item, list):
                parts.append(self.format_tuple(item))
            else:
                parts.append(str(item))
        return '(' + ', '.join(parts) + ')'
        
    def apply_builtin(self, name, arg):
        if name == 'Print' or name == 'print':
            if isinstance(arg, list):
                if len(arg) == 0:
                    print('nil')
                    return 'nil'
                else:
                    printable = self.format_tuple(arg)
                    print(printable,end="")
                    return printable
            if isinstance(arg, str):
                interpreted = arg.replace('\\n', '\n').replace('\\t', '\t')
                print(f"{interpreted}", end="")
                return arg
            else:
                print(f"{arg}", end="")
                return arg
        elif name == 'Isinteger':
            return 'true' if isinstance(arg, int) else 'false'
        elif name == 'Istuple':
            return 'true' if isinstance(arg, list) else 'false'
        elif name == 'Isstring':
            return 'true' if isinstance(arg, str) else 'false'
        elif name == 'Isdummy':
            return 'true' if arg == 'dummy' else 'false'
        elif name == 'Istruthvalue':
            return 'true' if arg in ['true', 'false'] else 'false'
        elif name == 'Isfunction':
            return 'true' if isinstance(arg, (Closure, Eta)) else 'false'
        elif name == 'Stem':
            return arg[0] if isinstance(arg, str) and arg else ''
        elif name == 'Stern':
            return arg[1:] if isinstance(arg, str) else ''
        elif name == 'Conc':
            return arg[0] + arg[1]
        elif name == 'Order':
            return int(len(arg)) if isinstance(arg, (str, list)) else '0'
        elif name == 'Null':
            return 'true' if not arg else 'false'
        elif name == 'ItoS':
            try:
                return str(int(arg))  # Ensure it handles strings of integers too
            except ValueError:
                raise TypeError("ItoS expects an integer or string representing an integer")
        elif name == 'aug':
            if not isinstance(arg, list) or len(arg) != 2:
                raise TypeError("aug expects a tuple of form (tuple, value)")
            base, element = arg
            if not isinstance(base, list):
                raise TypeError("aug: first argument must be a tuple (list)")
            return base + [element]
        else:
            raise ValueError(f"Unknown builtin function: {name}")

    def print_state(self, instr):
        print(f"\nInstruction: {instr}")
        print(f"Control: {list(reversed(self.control))}")
        print(f"Stack: {self.stack}")
        print(f"Current Env: e{self.current_env.index}")
        print(f"Environments: {[f'e{env.index}' for env in self.environments if not env.is_removed]}\n")

    def run(self):
        steps = 0
        MAX_STEPS = 100000  # Increased for deep recursion
        self.trace_log.clear()
        
        while self.control:
            steps += 1
            if steps > MAX_STEPS:
                print("🔁 Execution stopped: exceeded maximum steps (possible infinite loop).")
                print(f"Top of stack: {self.stack[-1] if self.stack else 'empty'}")
                break
                
            instr = self.control.pop()
            # self.print_state(instr)  # Debug info
            self.record_state(instr)

            # if instr.isdigit():
            #     self.stack.append(instr)
            if isinstance(instr, int):
                self.stack.append(instr)

            elif instr.startswith('λ'):
                lambda_header = instr[1:]  # e.g. x,y^1
                param_part, delta_part = lambda_header.split('^')
                params = param_part.split(',')
                delta_id = int(delta_part)
                closure = Closure(params, delta_id, self.current_env.index)
                self.stack.append(closure)

            elif instr.startswith('τ'):
                n = int(instr[1:])
                if len(self.stack) < n:
                    raise IndexError(f"Tuple construction expected {n} elements but got {len(self.stack)}")
                tup = [self.stack.pop() for _ in range(n)]
                #tup.reverse()  # Maintain proper order
                self.stack.append(tup)

            elif instr == 'γ':
                if len(self.stack) < 2:
                    raise IndexError("Stack underflow: expected 2 elements for γ")
                
                func = self.stack.pop()
                arg = self.stack.pop()

                if isinstance(func, str) and func in self.builtins:
                    if func in {'Conc', 'aug'}:
                        if len(self.stack) < 1:
                            raise IndexError(f"{func} requires 2 arguments")
                        arg2 = self.stack.pop()
                        temp = self.control.pop()
                        arg1 = arg
                        result = self.apply_builtin(func, [arg1, arg2])
                        self.stack.append(result)
                    else:
                        result = self.apply_builtin(func, arg)
                        self.stack.append(result)
                
                elif isinstance(func, list) and isinstance(arg, int):
                    # This is tuple selection, not function application
                    index = int(arg)
                    if 1 <= index <= len(func):
                        self.stack.append(func[index - 1])
                    else:
                        raise IndexError(f"Index {index} out of bounds for tuple {func}")

                elif func == '<Y*>':
                    if not isinstance(arg, Closure):
                        raise TypeError("Y* must be applied to a closure")
                    # Create eta node
                    eta = Eta(arg)
                    self.stack.append(eta)

                elif isinstance(func, Eta):
                    # Handle eta application - this is the key for deep recursion
                    eta = func
                    original_closure = eta.closure
                    
                    # Create new environment for the recursive call
                    new_env = Environment(self.env_counter, self.find_env_by_index(original_closure.env_index))
                    self.env_counter += 1
                    
                    # Bind the recursive function parameter to the eta itself
                    new_env.extend(original_closure.params[0], eta)
                    
                    self.environments.append(new_env)
                    self.control.append('γ')
                    # Add environment removal instruction
                    self.control.append(f'env_remove_{new_env.index}')
                    
                    # Load the body of the lambda
                    self.control.extend(reversed(self.control_structures[original_closure.delta_id]))
                    
                    # Switch to new environment
                    old_env = self.current_env
                    self.current_env = new_env
                    
                    # Push argument to stack
                    self.stack.append(arg)

                elif isinstance(func, Closure):
                    # Regular lambda application
                    closure_env = self.find_env_by_index(func.env_index)
                    new_env = Environment(self.env_counter, closure_env)
                    self.env_counter += 1
                    
                    # Bind parameters
                    if len(func.params) == 1:
                        new_env.extend(func.params[0], arg)
                    else:
                        # Multiple parameters - arg should be a tuple
                        if not isinstance(arg, list):
                            raise TypeError("Expected tuple for multi-parameter lambda")
                        for i, param in enumerate(func.params):
                            new_env.extend(param, arg[i])
                    
                    self.environments.append(new_env)
                    
                    # Add environment removal instruction
                    self.control.append(f'env_remove_{new_env.index}')
                    
                    # Load lambda body
                    self.control.extend(reversed(self.control_structures[func.delta_id]))
                    
                    # Switch environment
                    self.current_env = new_env

                else:
                    raise TypeError(f"Cannot apply non-function: {func}")

            elif instr.startswith('env_remove_'):
                # Handle environment removal
                env_index = int(instr.split('_')[2])
                env_to_remove = self.find_env_by_index(env_index)
                if env_to_remove:
                    env_to_remove.set_removed(True)
                
                # Find the next active environment
                for env in reversed(self.environments):
                    if not env.is_removed:
                        self.current_env = env
                        break

            elif instr in ['+', '-', '*', '/', '**', '<', '>', '<=', '>=', 'eq', 'ne', 'ls', 'gr', 'le', 'ge', 'or', '&']:
                if len(self.stack) < 2:
                    raise IndexError("Stack underflow on binary operation")
                right = self.stack.pop()
                left = self.stack.pop()
                result = self.apply_binary(instr, left, right)
                self.stack.append(result)

            elif instr in ['neg', 'not']:
                if len(self.stack) < 1:
                    raise IndexError("Stack underflow on unary operation")
                operand = self.stack.pop()
                result = self.apply_unary(instr, operand)
                self.stack.append(result)
            
            elif instr == 'aug':
                if len(self.stack) < 2:
                    raise IndexError("Stack underflow on aug")
                element = self.stack.pop()
                base = self.stack.pop()
                result = self.apply_builtin('aug', [base, element])
                self.stack.append(result)

            elif instr == 'β':
                if len(self.stack) < 1:
                    raise IndexError("Stack underflow: β expects condition on stack")
                if len(self.control) < 2:
                    raise IndexError("β expects 2 control structures (then, else)")
                    
                condition = self.stack.pop()
                else_delta = self.control.pop()  # else branch
                then_delta = self.control.pop()  # then branch
                
                if condition == 'true':
                    # Execute then branch
                    if then_delta.startswith('δ'):
                        delta_id = int(then_delta[1:])
                        self.control.extend(reversed(self.control_structures[delta_id]))
                    else:
                        self.control.append(then_delta)
                elif condition == 'false':
                    # Execute else branch  
                    if else_delta.startswith('δ'):
                        delta_id = int(else_delta[1:])
                        self.control.extend(reversed(self.control_structures[delta_id]))
                    else:
                        self.control.append(else_delta)
                else:
                    raise ValueError(f"Invalid condition for β: {condition}")
                
            elif instr in self.builtins:
                self.stack.append(instr)
            elif (instr.startswith("'") and instr.endswith("'")) or (instr.startswith('"') and instr.endswith('"')):
                self.stack.append(instr[1:-1])
            elif instr == '<Y*>':
                self.stack.append('<Y*>')
            elif instr == 'dummy':
                self.stack.append('dummy')
            elif instr in ['true', 'false']:
                self.stack.append(instr)
            elif instr == '<nil>':
                self.stack.append([])
                # continue
            else:
                # Treat as variable
                val = self.lookup(instr)
                self.stack.append(val)

        # print("\n=== FINAL STACK ===")
        # print(self.stack)
        print()
        return self.stack[0] if self.stack else None
