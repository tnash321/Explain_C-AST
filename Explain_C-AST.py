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

# AST Visitor: Detect loops + MPI/OpenMP calls
class LoopVisitor(c_ast.NodeVisitor):
    # Tracks loops (for/while), nesting depth, and any MPI/OpenMP function calls inside loops.
    def __init__(self):
        self.depth = 0
        self.max_depth = 0
        self.loop_count = 0

    def visit_For(self, node):
        self._enter_loop(node, "for")
        self.generic_visit(node)
        self._exit_loop()

    def visit_While(self, node):
        self._enter_loop(node, "while")
        self.generic_visit(node)
        self._exit_loop()

    def visit_FuncCall(self, node):
        # Called whenever a function call is encountered in the AST.
        # If inside a loop, check if it is an MPI or OpenMP function.
        func_name = ""
        if isinstance(node.name, c_ast.ID):
            func_name = node.name.name

        # Check for MPI function calls (start with MPI_)
        if func_name.startswith("MPI_"):
            print(f"  -> Found MPI call: {func_name} (inside loop at depth {self.depth})")

        # Check for OpenMP pragmas (omp_ functions)
        if func_name.startswith("omp_"):
            print(f"  -> Found OpenMP call: {func_name} (inside loop at depth {self.depth})")

        self.generic_visit(node)

    def _enter_loop(self, node, loop_type):
        # Update loop counters and print info when entering a loop.
        self.depth += 1
        self.loop_count += 1
        self.max_depth = max(self.max_depth, self.depth)

        line = node.coord.line if node.coord else "unknown"
        print(f"Found {loop_type}-loop at line {line}")
        print(f"Current nesting depth: {self.depth}")

    def _exit_loop(self):
        # Decrease depth when leaving a loop.
        self.depth -= 1

# Main function
def main(filename):
    fake_libc = os.path.join(os.path.dirname(__file__), "fake_libc_include")
    tmp_file = prepare_clean_file(filename, fake_libc)

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

    # Visit loops and MPI/OpenMP calls
    visitor = LoopVisitor()
    visitor.visit(ast)

    # Print summary
    print("\n----------- Summary -----------")
    print(f"Total loops found: {visitor.loop_count}")
    print(f"Maximum nesting depth: {visitor.max_depth}")

    print("\n\nAST Tree\n")
    ast.show()

        # Cleanup
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

# Command-line interface
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 Explain_C-AST.py <file.c>")
        sys.exit(1)
    main(sys.argv[1])
