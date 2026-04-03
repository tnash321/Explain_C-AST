# Created by: Tyler Nash
# CSCI 490: Capstone Project
# CSU Chico Spring 2026

# test program correctness: with pytest -v

import sys
import os
import re
from pycparser import parse_file, c_ast
import argparse

# Helper function to remove comments
def strip_comments(text):
    # Replace /* ... */ with the same number of newline characters
    def block_replacer(match):
        s = match.group(0)
        return "\n" * s.count("\n")

    text = re.sub(r"/\*.*?\*/", block_replacer, text, flags=re.DOTALL)

    # Remove // comments but keep the line itself
    text = re.sub(r"//.*", "", text)

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

def load_pragmas(filename):
    pragmas = set()
    with open(filename) as f:
        for i, line in enumerate(f, start=1):
            if "#pragma omp" in line:
                pragmas.add(i)
    return pragmas

class LoopInfo:
    # Stores info about a single loop
    def __init__(self, line, depth, loop_type):
        self.line = line                  # Line number of loop start
        self.depth = depth                # Nesting depth
        self.loop_type = loop_type        # "for" or "while"
        self.calls = []                   # Function calls inside this loop

        self.score = 100                  # Initialize parallelizable score
        self.pos_reasons = []             # Positive reasons for score
        self.neg_reasons = []             # Negative reasons for score

        self.contains_mpi = False         # True if MPI calls are found
        self.contains_omp = False         # True if OpenMP runtime calls are found
        self.no_dynamic_memory = True     # True if no dynamic memory detected
        self.no_io = True                 # True if no Input/Output detected

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

    # Translates loop info into plain english explanations
    def to_english(self, pragmas):
        notes = [] # Extra notes

        if (self.line - 1) in pragmas:
            notes.append("There is an OpenMP pragma directly above this loop.")

        if self.contains_mpi:
            notes.append("Contains MPI calls.")

        if self.contains_omp:
            notes.append("Contains OpenMP runtime calls.")

        if self.calls:
            notes.append("Function calls: " + ", ".join(self.calls))

        # Max score is 100/100
        self.score = min(self.score, 100)

        s = f"The {self.loop_type}-loop at line {self.line} scores {self.score}/100.\n"

        s += f"This loop has a time-complexity of {self.complexity}.\n\n"

        if self.score >= 80:
            s += "It loop is a good candidate for parallelisation.\n"
        elif self.score >= 50:
            s += "It loop could be parallelised, but there are some concerns.\n"
        else:
            s += "It loop is poorly suited for parallelisation.\n"

        if notes or self.pos_reasons or self.neg_reasons:
            s += "\nKey reasons for score:\n"

            s += "\nPositives:\n"
            if self.pos_reasons:
                for reason in self.pos_reasons:
                    s += f" • {reason}\n"
            else:
                s += f" • None detected\n"

            s += "\nNegatives:\n"
            if self.neg_reasons:
                for reason in self.neg_reasons:
                    s += f" • {reason}\n"
            else:
                s += " • None detected\n"

            if notes:
                s += f"\nMore info in above loop:\n"
                for note in notes:
                    s += f" • {note}\n"

        return s


# AST Visitor: Detect loops + MPI/OpenMP calls
class LoopVisitor(c_ast.NodeVisitor):
    # Tracks loops (for/while), nesting depth, and any MPI/OpenMP function calls inside loops.
    def __init__(self, global_vars):
        self.global_vars = global_vars
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
            loop.neg_reasons.append("Contains break statement. (-10)")

    def visit_Assignment(self, node):
        if not self.loop_stack:
            self.generic_visit(node)
            return

        loop = self.loop_stack[-1]

        # Only handle the simple case: variable assignment "x = ..."
        if isinstance(node.lvalue, c_ast.ID):
            var_name = node.lvalue.name

            # Global write check
            if var_name in self.global_vars:
                loop.score -= 50
                loop.neg_reasons.append(f"Writes to global variable '{var_name}', which may cause shared-state conflicts. (-50)")

            # Simple reduction check
            if node.op == "+=":
                loop.score -= 10
                loop.neg_reasons.append(f"Possible reduction on '{var_name}' (uses +=), it is not ideal as independent work. (-10)")

         # Scalar self‑use: x = f(x, …)
        if isinstance(node.lvalue, c_ast.ID):
            lhs = node.lvalue.name
            if self._uses_id(node.rvalue, lhs):
                loop.score -= 20
                loop.neg_reasons.append(f"Scalar loop-carried dependency on '{lhs}', preventing safe parallel execution. (-20)")

        # Array self‑use: arr[i] = f(arr[...], …)
        if isinstance(node.lvalue, c_ast.ArrayRef):
            # the base array name (ignore index)
            if isinstance(node.lvalue.name, c_ast.ID):
                arr_name = node.lvalue.name.name
                if self._uses_array(node.rvalue, arr_name):
                    loop.score -= 30
                    loop.neg_reasons.append(f"Loop-carried dependency on '{arr_name}', preventing safe parallel execution.  (-30)")

        # Always keep walking
        self.generic_visit(node)

    def _uses_id(self, expr, name):
        found = False
        class Finder(c_ast.NodeVisitor):
            def visit_ID(self, node):
                nonlocal found
                if node.name == name:
                    found = True
        Finder().visit(expr)
        return found

    def _uses_array(self, expr, arr_name):
        # Return True if expr contains any ArrayRef whose base name is arr_name.
        # This is a coarse check for arr[...] in the RHS.
        found = False
        class Finder(c_ast.NodeVisitor):
            def visit_ArrayRef(self, node):
                nonlocal found
                if isinstance(node.name, c_ast.ID) and node.name.name == arr_name:
                    found = True
        Finder().visit(expr)
        return found
            

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

                if func_name in ('malloc', 'calloc', 'realloc', 'free'):
                    current_loop.no_dynamic_memory = False
                    current_loop.score -= 15
                    current_loop.neg_reasons.append(f"Dynamic memory allocation inside '{func_name}', it may reduce performance and scalability. (-15)")

                if func_name in ('printf','fprintf','scanf','fscanf','printf'):
                    current_loop.no_io = False
                    current_loop.score -= 30
                    current_loop.neg_reasons.append(f"I/O operation inside '{func_name}', it may serialize execution and reduce parallel performance. (-30)")

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

        # Calculate loop complexity
        order = self.estimate_loop_order(node)
        loop.order = order
        loop.complexity = self.order_to_complexity(order)

        # If loop is nested, subtract from score
        if self.depth > 1:
            loop.score -= 10
            loop.neg_reasons.append("Nested loop increases complexity. (-10)")

        # For for-loops, extract loop variable, etc.
        if isinstance(node, c_ast.For) and isinstance(node.init, c_ast.DeclList):
            # set loop.loop_var as before…
            trip_est = self._estimate_trip_count(node)
            if trip_est is not None:
                if trip_est >= 1000:
                    loop.score += 15
                    loop.pos_reasons.append(f"Large iteration count, great to parallelize. (~{trip_est}) (+15)")
                elif trip_est >= 100:
                    loop.score += 5
                    loop.pos_reasons.append(f"Moderate iteration count, good to parallelize. (~{trip_est}) (+5)")

    def _estimate_trip_count(self, node):
        # Estimate the number of iterations for a simple 'for' loop.
        # Returns an integer if both bounds are integer constants,
        # or a default "large" threshold (e.g. 100) if only one bound is constant.
        # Returns None if nothing useful can be inferred.
        start = None
        end = None

        # Extract initial value: e.g. 'for (int i = 0; ...)'
        if isinstance(node.init, c_ast.DeclList):
            decls = node.init.decls
            if decls:
                decl = decls[0]
                # Only handle integer constants; ignore floats or chars
                init_val = getattr(decl, 'init', None)
                if isinstance(init_val, c_ast.Constant) and init_val.type == 'int':
                    val_str = init_val.value.strip()
                    # Account for optional leading '-' sign
                    if val_str.lstrip('-').isdigit():
                        start = int(val_str)

        # Extract loop bound: e.g. 'i < 1000'
        if isinstance(node.cond, c_ast.BinaryOp):
            right = getattr(node.cond, 'right', None)
            if isinstance(right, c_ast.Constant) and right.type == 'int':
                bound_str = right.value.strip()
                if bound_str.lstrip('-').isdigit():
                    end = int(bound_str)

        # If both start and end are constants, compute the difference
        if start is not None and end is not None:
            return abs(end - start)

        # If exactly one side is a constant, treat the loop as "large"
        if start is not None or end is not None:
            return 100  # or any other default threshold

        # Otherwise, trip count is unknown
        return None
    
    # Estimate loop complexity as an exponent:
    # -1   -> O(log n)
    # 0    -> O(1)
    # 1    -> O(n)
    # 2    -> O(n^2)
    # None -> Unknown
    def estimate_loop_order(self, node):
    # Only handle for-loops
        if not isinstance(node, c_ast.For):
            return None
        order = None

        # --- Estimate this loop by itself ---
        if isinstance(node.cond, c_ast.BinaryOp):
            right = node.cond.right

            # for (...; i < 100; ...)
            if isinstance(right, c_ast.Constant):
                order = 0   # O(1)

            # for (...; i < n; ...)
            elif isinstance(right, c_ast.ID):
                order = 1   # O(n)

                # for (...; i < n; i *= 2)
                if isinstance(node.next, c_ast.Assignment) and node.next.op == "*=":
                    order = -1   # O(log n)

        if order is None:
            return None

        # --- Check for nested O(n) loops ---
        if order == 1:
            for _, child in node.stmt.children():
                if isinstance(child, c_ast.For):
                    inner_order = self.estimate_loop_order(child)
                    if inner_order == 1:
                        return 2   # O(n^2)

        return order
    
    def order_to_complexity(self, order):
        if order is None:
            return "Unknown"

        if order == -1:
            return "O(log n)"

        if order == 0:
            return "O(1)"

        if order == 1:
            return "O(n)"

        if order == 2:
            return "O(n^2)"

        return f"O(n^{order})"



    def _exit_loop(self):
        loop = self.loop_stack.pop()
        if loop.no_dynamic_memory:
            loop.score += 10
            loop.pos_reasons.append("No dynamic memory allocation in loop (+10)")
        if loop.no_io:
            loop.score += 10
            loop.pos_reasons.append("No I/O operations in loop (+10)")
        self.depth -= 1

class GlobalCollector:
    def __init__(self):
        self.globals = set()

    def collect(self, ast):
        # In pycparser, file-scope declarations live in ast.ext
        for ext in ast.ext:
            if isinstance(ext, c_ast.Decl) and ext.name:
                self.globals.add(ext.name)

# Main function
def main(filename, mode, output_file = None):
    fake_libc = os.path.join(os.path.dirname(__file__), "fake_libc_include")
    tmp_file = prepare_clean_file(filename, fake_libc)

    pragmas = load_pragmas(tmp_file)

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

     # Collect global variables
    global_collector = GlobalCollector()
    global_collector.collect(ast)
    global_vars = global_collector.globals

    print("---------- Testing file ---------")
    print(filename)
    print("mode:", mode)
    print()

    # Visit loops and MPI/OpenMP calls
    visitor = LoopVisitor(global_vars)
    visitor.visit(ast)

    print("--------- Loop Analysis ---------")
        
    for loop in visitor.loops:
        if args.mode == "ast":
            output_file = "c_ast.txt"

            if sys.argv[3] != "":
                output_file = sys.argv[3]

            # with open(output_file, "w") as f:
            #     ast.show(buf=f, showcoord=True)

            # print(f"AST written to {output_file}\n")

        elif args.mode == "score":
            for loop in visitor.loops:
                print(f"Line {loop.line} -> {loop.score}")

        elif args.mode == "complexity":
            for loop in visitor.loops:
                print(f"Line {loop.line} -> {loop.complexity}")

        elif args.mode == "english":
            for loop in visitor.loops:
                print(loop.to_english(pragmas))

        else:
            print(loop.to_english(pragmas))
        print()

    # Print summary
    print("----------- Summary -----------")
    print(f"Total loops found: {visitor.loop_count}")
    print(f"Maximum nesting depth: {visitor.max_depth}")

    # Writes AST into a .txt file
    output_file = "c_ast.txt"

    if len(sys.argv) == 5 and sys.argv[4].endswith(".txt"):
        output_file = sys.argv[4]

    with open(output_file, "w") as f:
        print(f"AST written to {output_file}\n")
        ast.show(buf = f, showcoord = True)

    # Cleanup
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

# Command-line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("file", help="C file to analyze")

    parser.add_argument(
        "--mode",
        choices=["english", "score", "ast", "complexity"],
        default="english",
        help="Output mode"
    )

    parser.add_argument(
        "output",
        nargs="?",
        help="Optional output file (.txt only)"
    )

    args = parser.parse_args()

    if args.output and not args.output.lower().endswith(".txt"):
        parser.error("Output file must be a .txt file")

    main(args.file, args.mode, args.output)