# test_c_analyzer.py
import subprocess
import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parent
TEST_DIR = ROOT / "tests"
ANALYZER = ROOT / "Explain_C-AST.py"


def run_analyzer(c_path: pathlib.Path):
    result = subprocess.run(
        [sys.executable, str(ANALYZER), str(c_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    return result.returncode, result.stdout + result.stderr


C_FILES = sorted(TEST_DIR.glob("*.c"))

@pytest.mark.parametrize("c_file", C_FILES, ids=[f.name for f in C_FILES])
def test_c_files(c_file):
    code, output = run_analyzer(c_file)

    should_fail = c_file.name.startswith("bad_")

    if should_fail:
        assert code != 0, f"{c_file.name} should fail\n\n{output}"
    else:
        assert code == 0, f"{c_file.name} failed\n\n{output}"