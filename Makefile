# Makefile for RPAL Interpreter Project

PYTHON = python3
SCRIPT = myrpal.py

# Run RPAL interpreter
run:
	$(PYTHON) $(SCRIPT) $(file)

# Show Abstract Syntax Tree
ast:
	$(PYTHON) $(SCRIPT) $(file) -ast

# Show Standardized Tree
st:
	$(PYTHON) $(SCRIPT) $(file) -st

# Show Flattened Control Structure
flat:
	$(PYTHON) $(SCRIPT) $(file) -flat

# Show Optimized Flattened Control Structure
optflat:
	$(PYTHON) $(SCRIPT) $(file) -optflat

# Run CSE Machine with trace (uses optimized flattener)
cse:
	$(PYTHON) $(SCRIPT) $(file) -optflat -cse

# Show AST and Standardized Tree
allt:
	$(PYTHON) $(SCRIPT) $(file) -allt

# Clean bytecode files
clean:
	rm -rf __pycache__ *.pyc

# Avoid conflicts if files exist with these names
.PHONY: run ast st flat optflat cse allt clean
