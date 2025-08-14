RPAL INTERPRETER - QUICK START GUIDE
====================================

WHAT IS THIS?
This is an RPAL (Right-reference Pedagogical Algorithmic Language) interpreter 
that can run simple functional programming code.

HOW TO RUN:
-----------

1. Basic usage:
   python myrpal.py yourfile.rpal

2. To see help:
   python myrpal.py -h

3. To debug and see internal structures:
   python myrpal.py yourfile.rpal -ast     (shows syntax tree)
   python myrpal.py yourfile.rpal -cse     (shows execution steps)
   python myrpal.py yourfile.rpal -st      (shows standardized tree)

4. To run Sample test cases
    python test_rpal.py

5. How to Use This Makefile

make run file=test.rpal         # Run the program normally
make ast file=test.rpal         # Print AST only
make st file=test.rpal          # Print Standardized Tree
make flat file=test.rpal        # Print unoptimized flattened structure
make optflat file=test.rpal     # Print optimized flattened structure
make cse file=test.rpal         # Execute using CSE machine with trace
make allt file=test.rpal        # Print AST and ST
make clean                      # Clean cache and pyc files

EXAMPLE:
--------
Create a file called "test.rpal" with this content:

let x = 5 in (add x 3)

Then run:
python myrpal.py test.rpal

WHAT FILES DO I NEED?
---------------------
Make sure you have all these files and folders:
- myrpal.py (main file)
- utils/ folder
- Lexer/ folder  
- Parser/ folder
- Standardizer/ folder
- flattener/ folder
- CSE_Machine/ folder

TROUBLESHOOTING:
----------------
- Make sure your RPAL file has .rpal extension
- Check that all required folders and files are present
- Use -h flag to see all available options

That's it! Your RPAL interpreter is ready to use.