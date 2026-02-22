# Created by: Tyler Nash
# CSCI 490: Capstone Project
# CSU Chico Spring 2026

import sys
import os
import re
from pycparser import parse_file, c_ast

# Helper function to remove comments
def strip_comments(text):
    # Remove both /* */ block comments and // line comments from C code.
    # Pycparser cannot handle comments, so we must strip them.
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'//.*', '', text)
    return text

# Prepare a clean temporary file
def prepare_clean_file(source_path, headers_path):
    # Strip comments from the source file and all fake headers.
    # Write a temporary file for pycparser to parse.

    # Clean source file
    with open(source_path, "r") as f:
        source_text = f.read()
    clean_source = strip_comments(source_text)
    tmp_file = source_path + ".tmp.c"
    with open(tmp_file, "w") as f:
        f.write(clean_source)

    # Clean headers
    for root, _, files in os.walk(headers_path):
        for filename in files:
            header_path = os.path.join(root, filename)
            with open(header_path, "r") as f:
                text = f.read()
            clean_text = strip_comments(text)
            with open(header_path, "w") as f:
                f.write(clean_text)

    return tmp_file

class LoopInfo:
    # Stores info about a single loop
    def __init__(self, line, depth, loop_type):
        self.line = line                  # Line number of loop start
        self.depth = depth                # Nesting depth
        self.loop_type = loop_type        # "for" or "while"
        self.calls = []                   # Function calls inside this loop
        self.contains_mpi = False         # True if MPI calls are found
        self.contains_omp = False         # True if OpenMP runtime calls are found

        self.score = 100       # Initialize parallelizable score
        self.reasons = []      # Reasons for score

    def add_penalty(self, amount, reason):
        self.score -= amount
        self.reasons.append(reason)

    def show(self):
        # Print basic loop info (optional)
        print(f"Loop at line {self.line}")
        print(f"Type: {self.loop_type}")
        print(f"Nesting depth: {self.depth}")
        if self.calls:
            print("Function calls inside loop:", ", ".join(self.calls))
        if self.contains_mpi:
            print("Contains MPI calls")
        if self.contains_omp:
            print("Contains OpenMP calls")
    
def load_pragmas(filename):
    pragmas = set()
    with open(filename) as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        if "#pragma omp" in line:
            pragmas.add(i)

    return pragmas


# AST Visitor: Detect loops + MPI/OpenMP calls
class LoopVisitor(c_ast.NodeVisitor):
    # Tracks loops (for/while), nesting depth, and any MPI/OpenMP function calls inside loops.
    def __init__(self):
        self.depth = 0
        self.max_depth = 0
        self.loop_count = 0

        self.loop_stack = []
        self.loops = []

    def visit_For(self, node):
        self._enter_loop(node, "for")
        self.generic_visit(node)
        self._exit_loop()

    def visit_While(self, node):
        self._enter_loop(node, "while")
        self.generic_visit(node)
        self._exit_loop()

    # If loop has break statement, subtract score
    def visit_Break(self, node):
        if self.loop_stack:
            loop = self.loop_stack[-1]
            loop.score -= 10
            loop.reasons.append("Contains break statement")
            

    def visit_FuncCall(self, node):
        # Called whenever a function call is encountered in the AST.
        # If inside a loop, check if it is an MPI or OpenMP function.
        if isinstance(node.name, c_ast.ID):
            func_name = node.name.name

            if self.loop_stack:
                current_loop = self.loop_stack[-1]
                current_loop.calls.append(func_name)

                if func_name.startswith("MPI_"):
                    current_loop.contains_mpi = True

                if func_name.startswith("omp_"):
                    current_loop.contains_omp = True

                if func_name.startswith("printf"):
                    current_loop.reasons.append(f"Function {func_name} may slow down loop")
                    current_loop.score -= 15


        self.generic_visit(node)

    def _enter_loop(self, node, loop_type):
        # Update loop counters and print info when entering a loop.
        self.depth += 1
        self.loop_count += 1
        self.max_depth = max(self.max_depth, self.depth)

        line = node.coord.line if node.coord else "unknown"

        loop = LoopInfo(line, self.depth, loop_type)
        self.loop_stack.append(loop)
        self.loops.append(loop)

        # If loop is nested, subtract from score
        if self.depth > 1:
            loop.score -= 10
            loop.reasons.append("Nested loop increases complexity")

    def _exit_loop(self):
        # Decrease depth when leaving a loop.
        self.loop_stack.pop()
        self.depth -= 1

# Main function
def main(filename):
    pragmas = load_pragmas(filename)

    fake_libc = os.path.join(os.path.dirname(__file__), "fake_libc_include")
    tmp_file = prepare_clean_file(filename, fake_libc)

    # All of the arguments to be ignored
    c_args = [
        f"-I{fake_libc}",
        "-D__attribute__(x)=",
        "-D__extension__=",
        "-D__inline__=",
        "-D__restrict=",
        "-D__asm__=",
        "-D__volatile__=",
        "-CC",  # preserve line numbers
    ]

    # Parse the file into an AST
    ast = parse_file(tmp_file, use_cpp=True, cpp_args=c_args)
    print("--------- AST Analysis --------")
    print("Testing file:", filename)
    print()

    # Visit loops and MPI/OpenMP calls
    visitor = LoopVisitor()
    visitor.visit(ast)

    print("--------- Loop Analysis ---------")
        
    for loop in visitor.loops:
        print(f"Loop at line {loop.line}")
        print(f"Type: {loop.loop_type}")
        print(f"Nesting depth: {loop.depth}")

        if (loop.line - 1) in pragmas:
            print("OpenMP pragma detected above this loop")

        if loop.contains_mpi:
            print("Contains MPI calls")

        if loop.contains_omp:
            print("Contains OpenMP runtime calls")

        if loop.calls:
            print("Function calls inside loop:")
            for c in loop.calls:
                print(f"  - {c}")

        # Print parallelizable score if changed
        if loop.score != 100:
            print(f"Loop parallelizable score: {loop.score} for these reasons:")

            for reason in loop.reasons:
                print(f" - {reason}")

        print()

    # Print summary
    print("----------- Summary -----------")
    print(f"Total loops found: {visitor.loop_count}")
    print(f"Maximum nesting depth: {visitor.max_depth}")

    with open("c_ast.txt", "w") as f:
        ast.show(buf = f, showcoord = True)

    # Cleanup
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

# Command-line interface
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 Explain_C-AST.py <file.c>")
        sys.exit(1)
    main(sys.argv[1])
