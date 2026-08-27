"""
Akasha Integration Tests
======================

End-to-end tests: run complete .akasha programs through the full pipeline
and verify output matches expected results.
"""

import sys
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.compiler.lexer.lexer import Lexer
from akasha.compiler.parser.parser import Parser
from akasha.compiler.interpreter.interpreter import Interpreter
from akasha.compiler.interpreter.values import AkashaRuntimeError


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def run_program(source: str) -> str:
    """Run a Akasha program and return stdout."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        tokens = Lexer(source).tokenize()
        prog   = Parser(tokens).parse()
        interp = Interpreter()
        interp.execute(prog)
    finally:
        sys.stdout = old
    return buf.getvalue()


def run_file(filename: str) -> str:
    """Run a .akasha example file and return stdout."""
    path   = EXAMPLES_DIR / filename
    source = path.read_text(encoding="utf-8")
    return run_program(source)


# ── Example File Tests ────────────────────────────────────────────────────────

class TestExampleFiles:
    def test_hello_world(self):
        output = run_file("01_hello_world.akasha")
        assert "Namaste, Akasha!" in output
        assert "Hello, World!" in output

    def test_variables(self):
        output = run_file("02_variables.akasha")
        assert "Peru: Subhash" in output
        assert "Desham: India" in output
        assert "a + b = 13" in output

    def test_conditions(self):
        output = run_file("03_conditions.akasha")
        assert "Pedda manishi" in output   # adult
        assert "Grade: A" in output
        assert "Can enter" in output

    def test_functions(self):
        output = run_file("04_functions.akasha")
        assert "10 + 32 = 42" in output
        assert "Namaste, Ravi!" in output
        assert "5! = 120" in output

    def test_loops(self):
        output = run_file("05_loops.akasha")
        assert "manga" in output
        assert "Count: 1" in output
        assert "Odd: 1" in output
        assert "Odd: 9" in output

    def test_showcase(self):
        output = run_file("06_showcase.akasha")
        assert "Akasha v1" in output
        assert "FizzBuzz" in output
        assert "Before:" in output
        assert "After:" in output


# ── Inline Complete Programs ──────────────────────────────────────────────────

class TestCompletePrograms:
    def test_bubble_sort(self):
        output = run_program("""
karyam bubble_sort(arr) {
    viluva n = parimaanam(arr)
    prathi i lo 0..n {
        prathi j lo 0..(n - i - 1) {
            okavela arr[j] > arr[j + 1] {
                viluva temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
            }
        }
    }
    phalitham arr
}
viluva sorted = bubble_sort([5, 2, 8, 1, 9, 3])
cheppu(sorted)
""")
        assert "[1, 2, 3, 5, 8, 9]" in output

    def test_sum_of_squares(self):
        output = run_program("""
viluva nums = range(1, 6)
viluva squares = nums.map(muppu(x) => x * x)
viluva total = squares.reduce(muppu(acc, x) => acc + x, 0)
cheppu(total)
""")
        assert "55" in output  # 1+4+9+16+25

    def test_prime_checker(self):
        output = run_program("""
karyam is_prime(n) {
    okavela n < 2 { phalitham abaddham }
    prathi i lo 2..n {
        okavela i * i > n { aapu }
        okavela n % i == 0 { phalitham abaddham }
    }
    phalitham nijam
}
prathi n lo 1..20 {
    okavela is_prime(n) {
        cheppu(n)
    }
}
""")
        lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
        nums  = [int(l) for l in lines]
        assert nums == [2, 3, 5, 7, 11, 13, 17, 19]

    def test_accumulator_pattern(self):
        output = run_program("""
karyam make_counter() {
    viluva count = 0
    phalitham muppu() => {
        count = count + 1
        phalitham count
    }
}
viluva counter = make_counter()
cheppu(counter())
cheppu(counter())
cheppu(counter())
""")
        lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
        assert lines == ["1", "2", "3"]

    def test_string_operations(self):
        output = run_program("""
viluva s = "Namaste Akasha"
cheppu(s.upper())
cheppu(s.lower())
cheppu(s.length())
cheppu(s.contains("Akasha"))
cheppu(s.replace("Akasha", "World"))
""")
        assert "NAMASTE AKASHA" in output
        assert "namaste akasha" in output
        assert "14" in output
        assert "nijam" in output
        assert "Namaste World" in output


    def test_map_operations(self):
        output = run_program("""
viluva person = {"name": "Ravi", "age": 30, "city": "Hyderabad"}
cheppu(person["name"])
cheppu(person["age"])
cheppu(parimaanam(person))
""")
        assert "Ravi" in output
        assert "30" in output
        assert "3" in output

    def test_nested_data_structures(self):
        output = run_program("""
viluva matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
prathi row lo matrix {
    prathi elem lo row {
        cheppu(elem)
    }
}
""")
        lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
        nums  = [int(l) for l in lines]
        assert nums == list(range(1, 10))


# ── Security Tests ────────────────────────────────────────────────────────────

class TestSecurity:
    def test_secret_not_leakable(self):
        """Secrets should not be readable directly via cheppu."""
        with pytest.raises(AkashaRuntimeError):
            run_program("""
rahasyam password = "super_secret"
cheppu(password)
""")

    def test_bounds_check_array(self):
        """Array access must raise on out-of-bounds."""
        with pytest.raises(AkashaRuntimeError):
            run_program("""
viluva arr = [1, 2, 3]
cheppu(arr[10])
""")

    def test_undefined_variable_error(self):
        """Accessing undefined variable should raise."""
        with pytest.raises(AkashaRuntimeError):
            run_program("cheppu(totally_undefined_var)")
