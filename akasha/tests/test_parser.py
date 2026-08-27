"""
Akasha Parser Tests
=================

Tests that the parser produces the correct AST for all syntactic constructs.
Run with: pytest tests/test_parser.py -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.compiler.lexer.lexer import Lexer
from akasha.compiler.parser.parser import Parser, ParseError
from akasha.compiler.ast_nodes.nodes import (
    Program, IntLiteral, FloatLiteral, StringLiteral, FStringLiteral,
    BoolLiteral, NullLiteral, Identifier, BinaryOp, UnaryOp,
    Assignment, Call, ArrayLiteral, MapLiteral, TupleLiteral,
    VarDecl, ConstDecl, FunctionDecl, ReturnStmt, IfStmt,
    WhileStmt, ForEachStmt, LoopStmt, BreakStmt, ContinueStmt,
    MatchStmt, ExprStatement, Closure, MethodCall, FieldAccess,
    Block, Param,
)


def parse(source: str) -> Program:
    """Helper: lex + parse a source string."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def parse_expr(source: str):
    """Parse a single expression, return the expression node."""
    prog = parse(source)
    assert len(prog.body) == 1
    stmt = prog.body[0]
    if isinstance(stmt, ExprStatement):
        return stmt.expr
    return stmt


# ── Literal Parsing ───────────────────────────────────────────────────────────

class TestLiteralParsing:
    def test_integer(self):
        node = parse_expr("42")
        assert isinstance(node, IntLiteral)
        assert node.value == 42

    def test_hex_integer(self):
        node = parse_expr("0xFF")
        assert isinstance(node, IntLiteral)
        assert node.value == 255

    def test_float(self):
        node = parse_expr("3.14")
        assert isinstance(node, FloatLiteral)
        assert abs(node.value - 3.14) < 1e-10

    def test_string(self):
        node = parse_expr('"hello"')
        assert isinstance(node, StringLiteral)
        assert node.value == "hello"

    def test_bool_true(self):
        node = parse_expr("nijam")
        assert isinstance(node, BoolLiteral)
        assert node.value is True

    def test_bool_false(self):
        node = parse_expr("abaddham")
        assert isinstance(node, BoolLiteral)
        assert node.value is False

    def test_null(self):
        node = parse_expr("shunyam")
        assert isinstance(node, NullLiteral)

    def test_fstring(self):
        node = parse_expr('f"Hello, {name}!"')
        assert isinstance(node, FStringLiteral)
        assert len(node.parts) >= 2  # "Hello, " + name + "!"

    def test_array_empty(self):
        node = parse_expr("[]")
        assert isinstance(node, ArrayLiteral)
        assert node.elements == []

    def test_array_literals(self):
        node = parse_expr("[1, 2, 3]")
        assert isinstance(node, ArrayLiteral)
        assert len(node.elements) == 3

    def test_map_empty(self):
        node = parse_expr("{}")
        assert isinstance(node, MapLiteral)
        assert node.pairs == []

    def test_tuple(self):
        node = parse_expr("(1, 2, 3)")
        assert isinstance(node, TupleLiteral)
        assert len(node.elements) == 3


# ── Expression Parsing ────────────────────────────────────────────────────────

class TestExpressionParsing:
    def test_addition(self):
        node = parse_expr("1 + 2")
        assert isinstance(node, BinaryOp)
        assert node.operator == "+"
        assert isinstance(node.left,  IntLiteral)
        assert isinstance(node.right, IntLiteral)

    def test_operator_precedence_mul_over_add(self):
        # 2 + 3 * 4  should parse as  2 + (3 * 4)
        node = parse_expr("2 + 3 * 4")
        assert isinstance(node, BinaryOp)
        assert node.operator == "+"
        assert isinstance(node.right, BinaryOp)
        assert node.right.operator == "*"

    def test_parentheses_override_precedence(self):
        # (2 + 3) * 4  should parse as  (2+3) * 4
        node = parse_expr("(2 + 3) * 4")
        assert isinstance(node, BinaryOp)
        assert node.operator == "*"
        assert isinstance(node.left, BinaryOp)

    def test_power_operator(self):
        node = parse_expr("2 ** 8")
        assert isinstance(node, BinaryOp)
        assert node.operator == "**"

    def test_unary_negate(self):
        node = parse_expr("-42")
        assert isinstance(node, UnaryOp)
        assert node.operator == "-"

    def test_unary_not(self):
        node = parse_expr("!nijam")
        assert isinstance(node, UnaryOp)
        assert node.operator == "!"

    def test_comparison(self):
        node = parse_expr("x >= 18")
        assert isinstance(node, BinaryOp)
        assert node.operator == ">="

    def test_equality(self):
        node = parse_expr("a == b")
        assert isinstance(node, BinaryOp)
        assert node.operator == "=="

    def test_logical_and(self):
        node = parse_expr("a && b")
        assert isinstance(node, BinaryOp)
        assert node.operator == "&&"

    def test_logical_or(self):
        node = parse_expr("a || b")
        assert isinstance(node, BinaryOp)
        assert node.operator == "||"

    def test_assignment(self):
        node = parse_expr("x = 42")
        assert isinstance(node, Assignment)
        assert node.name == "x"

    def test_function_call_no_args(self):
        node = parse_expr("cheppu()")
        assert isinstance(node, Call)
        assert isinstance(node.callee, Identifier)
        assert node.callee.name == "cheppu"
        assert node.arguments == []

    def test_function_call_with_args(self):
        node = parse_expr('cheppu("hello", 42)')
        assert isinstance(node, Call)
        assert len(node.arguments) == 2

    def test_method_call(self):
        node = parse_expr("arr.map(fn)")
        assert isinstance(node, MethodCall)
        assert node.method == "map"

    def test_field_access(self):
        node = parse_expr("obj.field")
        assert isinstance(node, FieldAccess)
        assert node.field == "field"

    def test_closure(self):
        node = parse_expr("muppu(x) => x * 2")
        assert isinstance(node, Closure)
        assert len(node.params) == 1
        assert node.params[0].name == "x"


# ── Statement Parsing ─────────────────────────────────────────────────────────

class TestStatementParsing:
    def test_var_decl(self):
        prog = parse("viluva x = 42")
        assert len(prog.body) == 1
        stmt = prog.body[0]
        assert isinstance(stmt, VarDecl)
        assert stmt.name == "x"
        assert isinstance(stmt.value, IntLiteral)

    def test_const_decl(self):
        prog = parse("sthiram PI = 3.14")
        stmt = prog.body[0]
        assert isinstance(stmt, ConstDecl)
        assert stmt.name == "PI"

    def test_var_decl_with_type(self):
        prog = parse("viluva x: Sankhya = 10")
        stmt = prog.body[0]
        assert isinstance(stmt, VarDecl)
        assert stmt.type_ is not None
        assert stmt.type_.name == "Sankhya"

    def test_function_decl_no_params(self):
        prog = parse("karyam hello() { cheppu(\"hi\") }")
        stmt = prog.body[0]
        assert isinstance(stmt, FunctionDecl)
        assert stmt.name == "hello"
        assert stmt.params == []

    def test_function_decl_with_params(self):
        prog = parse("karyam add(a, b) { phalitham a + b }")
        stmt = prog.body[0]
        assert isinstance(stmt, FunctionDecl)
        assert len(stmt.params) == 2
        assert stmt.params[0].name == "a"
        assert stmt.params[1].name == "b"

    def test_function_with_return_type(self):
        prog = parse("karyam get(): Sankhya { phalitham 42 }")
        stmt = prog.body[0]
        assert isinstance(stmt, FunctionDecl)
        assert stmt.return_type is not None
        assert stmt.return_type.name == "Sankhya"

    def test_return_stmt(self):
        prog = parse("karyam f() { phalitham 42 }")
        fn = prog.body[0]
        ret = fn.body.body[0]
        assert isinstance(ret, ReturnStmt)

    def test_if_stmt_simple(self):
        prog = parse("okavela x > 0 { cheppu(x) }")
        stmt = prog.body[0]
        assert isinstance(stmt, IfStmt)
        assert isinstance(stmt.condition, BinaryOp)
        assert stmt.else_block is None

    def test_if_else_stmt(self):
        prog = parse("okavela x > 0 { cheppu(1) } lekapothe { cheppu(0) }")
        stmt = prog.body[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.else_block is not None

    def test_if_elif_else(self):
        prog = parse("""
okavela x > 10 { cheppu("big") }
mariyu x > 5 { cheppu("med") }
lekapothe { cheppu("small") }
""")
        stmt = prog.body[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.elif_arms) == 1
        assert stmt.else_block is not None

    def test_while_stmt(self):
        prog = parse("alaa x > 0 { x = x - 1 }")
        stmt = prog.body[0]
        assert isinstance(stmt, WhileStmt)

    def test_for_each_stmt(self):
        prog = parse("prathi i lo 1..10 { cheppu(i) }")
        stmt = prog.body[0]
        assert isinstance(stmt, ForEachStmt)
        assert stmt.var == "i"

    def test_loop_stmt(self):
        prog = parse("loop { aapu }")
        stmt = prog.body[0]
        assert isinstance(stmt, LoopStmt)

    def test_break_stmt(self):
        prog = parse("loop { aapu }")
        body = prog.body[0].body.body
        assert isinstance(body[0], BreakStmt)

    def test_continue_stmt(self):
        prog = parse("loop { konasaginchu }")
        body = prog.body[0].body.body
        assert isinstance(body[0], ContinueStmt)

    def test_match_stmt(self):
        prog = parse("""
tirugu x {
    sthithi 1 => cheppu("one")
    default   => cheppu("other")
}
""")
        stmt = prog.body[0]
        assert isinstance(stmt, MatchStmt)
        assert len(stmt.arms) == 1
        assert stmt.default is not None


# ── Multiple Statements ───────────────────────────────────────────────────────

class TestMultipleStatements:
    def test_multiple_statements(self):
        prog = parse("viluva x = 1\nviluva y = 2\ncheppu(x)")
        assert len(prog.body) == 3

    def test_nested_function(self):
        prog = parse("""
karyam outer() {
    karyam inner() {
        phalitham 42
    }
    phalitham inner()
}
""")
        outer = prog.body[0]
        assert isinstance(outer, FunctionDecl)
        inner = outer.body.body[0]
        assert isinstance(inner, FunctionDecl)


# ── Error Recovery ────────────────────────────────────────────────────────────

class TestParseErrors:
    def test_missing_closing_paren(self):
        with pytest.raises(ParseError):
            parse("cheppu(42")

    def test_missing_closing_brace(self):
        with pytest.raises(ParseError):
            parse("okavela x { cheppu(x)")

    def test_missing_lo_in_for(self):
        with pytest.raises(ParseError):
            parse("prathi i 1..10 { }")

    def test_invalid_token_in_expr(self):
        with pytest.raises(Exception):
            parse("@ invalid")
