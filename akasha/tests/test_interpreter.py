"""
Akasha Interpreter Tests
======================

Tests the full pipeline: source code → Lexer → Parser → Interpreter → output.
Verifies runtime behavior of all v0.1 features.
Run with: pytest tests/test_interpreter.py -v
"""

import sys
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.compiler.lexer.lexer import Lexer
from akasha.compiler.parser.parser import Parser
from akasha.compiler.interpreter.interpreter import Interpreter
from akasha.compiler.interpreter.values import (
    AkashaInt, AkashaFloat, AkashaString, AkashaBool, AkashaNullType,
    AkashaArray, AkashaMap, AkashaTuple,
    AkashaRuntimeError, SHUNYAM
)


def run(source: str) -> any:
    """Execute source, return the last evaluated value."""
    tokens = Lexer(source).tokenize()
    prog   = Parser(tokens).parse()
    interp = Interpreter()
    interp.execute(prog)
    return interp


def eval_expr(source: str) -> any:
    """Evaluate a single expression and return its Akasha value."""
    tokens = Lexer(source).tokenize()
    prog   = Parser(tokens).parse()
    interp = Interpreter()
    from akasha.compiler.ast_nodes.nodes import ExprStatement
    stmt = prog.body[0]
    if isinstance(stmt, ExprStatement):
        return interp.execute_expression(stmt.expr)
    return interp.execute(prog)


def get_var(source: str, name: str) -> any:
    """Run source, return value of variable 'name'."""
    tokens = Lexer(source).tokenize()
    prog   = Parser(tokens).parse()
    interp = Interpreter()
    interp.execute(prog)
    return interp._globals.get(name)


def capture_output(source: str) -> str:
    """Run source and capture stdout."""
    tokens  = Lexer(source).tokenize()
    prog    = Parser(tokens).parse()
    interp  = Interpreter()
    buf     = io.StringIO()
    old_out = sys.stdout
    sys.stdout = buf
    try:
        interp.execute(prog)
    finally:
        sys.stdout = old_out
    return buf.getvalue()


# ── Literals ──────────────────────────────────────────────────────────────────

class TestLiterals:
    def test_integer(self):
        v = eval_expr("42")
        assert isinstance(v, AkashaInt)
        assert v.value == 42

    def test_negative_integer(self):
        v = eval_expr("-17")
        assert isinstance(v, AkashaInt)
        assert v.value == -17

    def test_float(self):
        v = eval_expr("3.14")
        assert isinstance(v, AkashaFloat)
        assert abs(v.value - 3.14) < 1e-10

    def test_string(self):
        v = eval_expr('"namaste"')
        assert isinstance(v, AkashaString)
        assert v.value == "namaste"

    def test_bool_true(self):
        v = eval_expr("nijam")
        assert isinstance(v, AkashaBool)
        assert v.value is True

    def test_bool_false(self):
        v = eval_expr("abaddham")
        assert isinstance(v, AkashaBool)
        assert v.value is False

    def test_null(self):
        v = eval_expr("shunyam")
        assert isinstance(v, AkashaNullType)


# ── Arithmetic ────────────────────────────────────────────────────────────────

class TestArithmetic:
    def test_addition(self):
        v = eval_expr("10 + 32")
        assert isinstance(v, AkashaInt)
        assert v.value == 42

    def test_subtraction(self):
        v = eval_expr("100 - 58")
        assert isinstance(v, AkashaInt)
        assert v.value == 42

    def test_multiplication(self):
        v = eval_expr("6 * 7")
        assert isinstance(v, AkashaInt)
        assert v.value == 42

    def test_division(self):
        v = eval_expr("84 / 2")
        assert v.value == 42.0

    def test_integer_division_via_floor(self):
        v = eval_expr("7 / 2")
        assert v.value == 3.5

    def test_modulo(self):
        v = eval_expr("10 % 3")
        assert isinstance(v, AkashaInt)
        assert v.value == 1

    def test_power(self):
        v = eval_expr("2 ** 10")
        assert v.value == 1024

    def test_operator_precedence(self):
        v = eval_expr("2 + 3 * 4")
        assert v.value == 14

    def test_float_arithmetic(self):
        v = eval_expr("1.5 + 2.5")
        assert isinstance(v, AkashaFloat)
        assert v.value == 4.0

    def test_string_concat(self):
        v = eval_expr('"hello" + " " + "world"')
        assert isinstance(v, AkashaString)
        assert v.value == "hello world"

    def test_division_by_zero(self):
        with pytest.raises(AkashaRuntimeError):
            eval_expr("1 / 0")

    def test_modulo_by_zero(self):
        with pytest.raises(AkashaRuntimeError):
            eval_expr("5 % 0")


# ── Comparisons ───────────────────────────────────────────────────────────────

class TestComparisons:
    def test_equal_true(self):
        v = eval_expr("5 == 5")
        assert v.value is True

    def test_equal_false(self):
        v = eval_expr("5 == 6")
        assert v.value is False

    def test_not_equal(self):
        v = eval_expr("5 != 6")
        assert v.value is True

    def test_less_than(self):
        v = eval_expr("3 < 5")
        assert v.value is True

    def test_less_equal(self):
        v = eval_expr("5 <= 5")
        assert v.value is True

    def test_greater_than(self):
        v = eval_expr("10 > 5")
        assert v.value is True

    def test_greater_equal(self):
        v = eval_expr("5 >= 5")
        assert v.value is True

    def test_string_equality(self):
        v = eval_expr('"abc" == "abc"')
        assert v.value is True

    def test_null_equality(self):
        v = eval_expr("shunyam == shunyam")
        assert v.value is True


# ── Logical Operators ─────────────────────────────────────────────────────────

class TestLogical:
    def test_and_true(self):
        v = eval_expr("nijam && nijam")
        assert v.value is True

    def test_and_false(self):
        v = eval_expr("nijam && abaddham")
        assert v.value is False

    def test_or_true(self):
        v = eval_expr("abaddham || nijam")
        assert v.value is True

    def test_or_false(self):
        v = eval_expr("abaddham || abaddham")
        assert v.value is False

    def test_not_true(self):
        v = eval_expr("!abaddham")
        assert v.value is True

    def test_not_false(self):
        v = eval_expr("!nijam")
        assert v.value is False


# ── Variables ─────────────────────────────────────────────────────────────────

class TestVariables:
    def test_var_decl_and_lookup(self):
        v = get_var("viluva x = 42", "x")
        assert isinstance(v, AkashaInt)
        assert v.value == 42

    def test_const_decl(self):
        v = get_var("sthiram PI = 3.14", "PI")
        assert isinstance(v, AkashaFloat)

    def test_var_assignment(self):
        v = get_var("viluva x = 10\nx = x + 5", "x")
        assert v.value == 15

    def test_multiple_vars(self):
        interp_source = "viluva a = 1\nviluva b = 2\nviluva c = a + b"
        v = get_var(interp_source, "c")
        assert v.value == 3

    def test_string_var(self):
        v = get_var('viluva name = "Subhash"', "name")
        assert isinstance(v, AkashaString)
        assert v.value == "Subhash"

    def test_undefined_var(self):
        with pytest.raises(AkashaRuntimeError):
            get_var("viluva x = 1", "y")


# ── Collections ───────────────────────────────────────────────────────────────

class TestCollections:
    def test_array_literal(self):
        v = eval_expr("[1, 2, 3]")
        assert isinstance(v, AkashaArray)
        assert len(v.elements) == 3

    def test_array_index(self):
        v = eval_expr("[10, 20, 30][1]")
        assert isinstance(v, AkashaInt)
        assert v.value == 20

    def test_array_index_out_of_bounds(self):
        with pytest.raises(AkashaRuntimeError):
            eval_expr("[1, 2][5]")

    def test_array_negative_index(self):
        v = eval_expr("[1, 2, 3][-1]")
        assert v.value == 3

    def test_map_literal(self):
        v = eval_expr('{"key": 42}')
        assert isinstance(v, AkashaMap)

    def test_map_access(self):
        v = eval_expr('{"a": 1, "b": 2}["a"]')
        assert v.value == 1

    def test_tuple_literal(self):
        v = eval_expr("(1, 2, 3)")
        assert isinstance(v, AkashaTuple)
        assert len(v.elements) == 3

    def test_array_cherchu(self):
        output = capture_output("""
viluva arr = [1, 2, 3]
arr.cherchu(4)
cheppu(parimaanam(arr))
""")
        assert "4" in output

    def test_array_map(self):
        v = get_var("""
viluva nums = [1, 2, 3]
viluva doubled = nums.map(muppu(x) => x * 2)
""", "doubled")
        assert isinstance(v, AkashaArray)
        assert v.elements[0].value == 2
        assert v.elements[1].value == 4
        assert v.elements[2].value == 6

    def test_array_filter(self):
        v = get_var("""
viluva nums = [1, 2, 3, 4, 5]
viluva evens = nums.filter(muppu(x) => x % 2 == 0)
""", "evens")
        assert isinstance(v, AkashaArray)
        assert len(v.elements) == 2


# ── Conditions ────────────────────────────────────────────────────────────────

class TestConditions:
    def test_if_true(self):
        output = capture_output("okavela nijam { cheppu(\"yes\") }")
        assert "yes" in output

    def test_if_false_no_output(self):
        output = capture_output("okavela abaddham { cheppu(\"yes\") }")
        assert "yes" not in output

    def test_if_else_true(self):
        output = capture_output("""
okavela nijam { cheppu("yes") } lekapothe { cheppu("no") }
""")
        assert "yes" in output
        assert "no" not in output

    def test_if_else_false(self):
        output = capture_output("""
okavela abaddham { cheppu("yes") } lekapothe { cheppu("no") }
""")
        assert "no" in output

    def test_if_elif_else(self):
        output = capture_output("""
viluva x = 85
okavela x >= 90 { cheppu("A+") }
mariyu x >= 80 { cheppu("A") }
lekapothe { cheppu("B") }
""")
        assert "A\n" in output

    def test_match_basic(self):
        output = capture_output("""
viluva color = "erra"
tirugu color {
    sthithi "erra"   => cheppu("Red")
    sthithi "neelam" => cheppu("Blue")
    default          => cheppu("Unknown")
}
""")
        assert "Red" in output

    def test_match_default(self):
        output = capture_output("""
viluva x = "purple"
tirugu x {
    sthithi "red" => cheppu("Red")
    default       => cheppu("Other")
}
""")
        assert "Other" in output


# ── Functions ─────────────────────────────────────────────────────────────────

class TestFunctions:
    def test_simple_function(self):
        output = capture_output("""
karyam hello() {
    cheppu("Namaste!")
}
hello()
""")
        assert "Namaste!" in output

    def test_function_with_return(self):
        v = get_var("""
karyam add(a, b) {
    phalitham a + b
}
viluva result = add(10, 32)
""", "result")
        assert v.value == 42

    def test_default_parameter(self):
        output = capture_output("""
karyam greet(name = "World") {
    cheppu(f"Hello, {name}!")
}
greet()
greet("Akasha")
""")
        assert "Hello, World!" in output
        assert "Hello, Akasha!" in output

    def test_recursion_factorial(self):
        v = get_var("""
karyam factorial(n) {
    okavela n <= 1 { phalitham 1 }
    phalitham n * factorial(n - 1)
}
viluva result = factorial(5)
""", "result")
        assert v.value == 120

    def test_closure(self):
        v = get_var("""
viluva square = muppu(x) => x * x
viluva result = square(7)
""", "result")
        assert v.value == 49

    def test_closure_captures_outer(self):
        v = get_var("""
karyam make_adder(n) {
    phalitham muppu(x) => x + n
}
viluva add5 = make_adder(5)
viluva result = add5(10)
""", "result")
        assert v.value == 15

    def test_higher_order_function(self):
        v = get_var("""
karyam apply(fn, value) {
    phalitham fn(value)
}
karyam double(x) { phalitham x * 2 }
viluva result = apply(double, 21)
""", "result")
        assert v.value == 42

    def test_function_not_found(self):
        with pytest.raises(AkashaRuntimeError):
            run("undefined_function()")


# ── Loops ─────────────────────────────────────────────────────────────────────

class TestLoops:
    def test_for_each_array(self):
        output = capture_output("""
prathi x lo [1, 2, 3] {
    cheppu(x)
}
""")
        assert "1\n2\n3" in output.strip()

    def test_for_each_range(self):
        output = capture_output("""
prathi i lo 1..4 {
    cheppu(i)
}
""")
        assert "1\n2\n3" in output

    def test_while_loop(self):
        v = get_var("""
viluva i = 0
viluva sum = 0
alaa i < 5 {
    sum = sum + i
    i = i + 1
}
""", "sum")
        assert v.value == 10  # 0+1+2+3+4

    def test_loop_with_break(self):
        v = get_var("""
viluva count = 0
loop {
    count = count + 1
    okavela count >= 5 { aapu }
}
""", "count")
        assert v.value == 5

    def test_for_with_continue(self):
        output = capture_output("""
prathi i lo 1..6 {
    okavela i % 2 == 0 { konasaginchu }
    cheppu(i)
}
""")
        lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
        nums  = [int(l) for l in lines]
        assert nums == [1, 3, 5]

    def test_nested_loops(self):
        v = get_var("""
viluva total = 0
prathi i lo 1..4 {
    prathi j lo 1..4 {
        total = total + 1
    }
}
""", "total")
        assert v.value == 9   # 3x3


# ── F-strings ─────────────────────────────────────────────────────────────────

class TestFStrings:
    def test_simple_fstring(self):
        output = capture_output("""
viluva name = "Akasha"
cheppu(f"Hello, {name}!")
""")
        assert "Hello, Akasha!" in output

    def test_fstring_with_arithmetic(self):
        output = capture_output("""
viluva x = 5
cheppu(f"Square: {x * x}")
""")
        assert "Square: 25" in output

    def test_fstring_multiple_vars(self):
        output = capture_output("""
viluva a = 10
viluva b = 20
cheppu(f"{a} + {b} = {a + b}")
""")
        assert "10 + 20 = 30" in output


# ── Built-in Functions ────────────────────────────────────────────────────────

class TestBuiltins:
    def test_cheppu(self):
        output = capture_output('cheppu("test")')
        assert "test" in output

    def test_cheppu_multiple_args(self):
        output = capture_output('cheppu("a", "b", "c")')
        assert "a b c" in output

    def test_parimaanam_array(self):
        v = eval_expr("parimaanam([1, 2, 3])")
        assert v.value == 3

    def test_parimaanam_string(self):
        v = eval_expr('parimaanam("hello")')
        assert v.value == 5

    def test_type_of_int(self):
        v = eval_expr("type_of(42)")
        assert v.value == "Sankhya"

    def test_type_of_string(self):
        v = eval_expr('type_of("hello")')
        assert v.value == "Padam"

    def test_sankhya_conversion(self):
        v = eval_expr('Sankhya("42")')
        assert v.value == 42

    def test_dasamsam_conversion(self):
        v = eval_expr("Dasamsam(42)")
        assert isinstance(v, AkashaFloat)

    def test_padam_conversion(self):
        v = eval_expr("Padam(42)")
        assert isinstance(v, AkashaString)
        assert v.value == "42"

    def test_range_builtin(self):
        v = eval_expr("range(5)")
        assert isinstance(v, AkashaArray)
        assert len(v.elements) == 5


# ── Integration Tests ─────────────────────────────────────────────────────────

class TestIntegration:
    def test_hello_world(self):
        output = capture_output('cheppu("Namaste, Akasha!")')
        assert "Namaste, Akasha!" in output

    def test_fizzbuzz(self):
        output = capture_output("""
karyam fizzbuzz(n) {
    okavela n % 15 == 0 { phalitham "FizzBuzz" }
    mariyu n % 3 == 0   { phalitham "Fizz" }
    mariyu n % 5 == 0   { phalitham "Buzz" }
    lekapothe            { phalitham Padam(n) }
}
prathi i lo 1..16 {
    cheppu(fizzbuzz(i))
}
""")
        lines = output.strip().split("\n")
        assert lines[2]  == "Fizz"    # 3
        assert lines[4]  == "Buzz"    # 5
        assert lines[14] == "FizzBuzz" # 15

    def test_fibonacci(self):
        v = get_var("""
karyam fib(n) {
    okavela n <= 1 { phalitham n }
    phalitham fib(n-1) + fib(n-2)
}
viluva result = fib(10)
""", "result")
        assert v.value == 55

    def test_scope_isolation(self):
        v = get_var("""
viluva x = 100
karyam get_local() {
    viluva x = 42
    phalitham x
}
viluva local = get_local()
""", "x")
        assert v.value == 100  # outer x not modified

    def test_array_operations_chain(self):
        v = get_var("""
viluva nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
viluva result = nums.filter(muppu(x) => x % 2 == 0).map(muppu(x) => x * x)
""", "result")
        assert isinstance(v, AkashaArray)
        # even numbers squared: 4, 16, 36, 64, 100
        vals = [e.value for e in v.elements]
        assert vals == [4, 16, 36, 64, 100]
