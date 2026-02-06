import sys
import os
import re
from pycparser import parse_file, c_ast


# ===============================
# Helper: Strip comments from a file
# ===============================
def strip_comments(text):
    # Remove /* */ comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove // comments
    text = re.sub(r'//.*', '', text)
    return text


# ===============================
# Helper: Strip comments from C source and headers
# ===============================
def prepare_clean_file(source_path, headers_path):
    # --- Clean source file ---
    with open(source_path, "r") as f:
        source_text = f.read()
    clean_source = strip_comments(source_text)
    tmp_file = source_path + ".tmp.c"
    with open(tmp_file, "w") as f:
        f.write(clean_source)

    # --- Clean headers in fake_libc_include ---
    for root, _, files in os.walk(headers_path):
        for filename in files:
            header_path = os.path.join(root, filename)
            with open(header_path, "r") as f:
                text = f.read()
            clean_text = strip_comments(text)
            with open(header_path, "w") as f:
                f.write(clean_text)

    return tmp_file


# ===============================
# AST Visitor: Detect loops
# ===============================
class LoopVisitor(c_ast.NodeVisitor):
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

    def _enter_loop(self, node, loop_type):
        self.depth += 1
        self.loop_count += 1
        self.max_depth = max(self.max_depth, self.depth)
        line = node.coord.line if node.coord else "unknown"
        print(f"Found {loop_type}-loop at line {line}")
        print(f"Current nesting depth: {self.depth}")

    def _exit_loop(self):
        self.depth -= 1


# ===============================
# Main analysis function
# ===============================
def main(filename):
    # -------------------------------
    # Step 1: Prepare clean source and headers
    # -------------------------------
    fake_libc = os.path.join(os.path.dirname(__file__), "fake_libc_include")
    tmp_file = prepare_clean_file(filename, fake_libc)

    # -------------------------------
    # Step 2: Set up cpp arguments
    # -------------------------------
    cpp_args = [
        f"-I{fake_libc}",
        "-D__attribute__(x)=",
        "-D__extension__=",
        "-D__inline__=",
        "-D__restrict=",
        "-D__asm__=",
        "-D__volatile__=",
        "-CC",  # preserve line numbers
    ]

    # -------------------------------
    # Step 3: Parse file into AST
    # -------------------------------
    ast = parse_file(tmp_file, use_cpp=True, cpp_args=cpp_args)
    print("=== AST Analysis ===")

    # -------------------------------
    # Step 4: Visit loops
    # -------------------------------
    visitor = LoopVisitor()
    visitor.visit(ast)

    # -------------------------------
    # Step 5: Print summary
    # -------------------------------
    print("\n=== Summary ===")
    print(f"Total loops found: {visitor.loop_count}")
    print(f"Maximum nesting depth: {visitor.max_depth}")

    # -------------------------------
    # Step 6: Cleanup temporary file
    # -------------------------------
    os.remove(tmp_file)


# ===============================
# Command-line interface
# ===============================
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 Explain_C-AST.py <file.c>")
        sys.exit(1)
    main(sys.argv[1])
