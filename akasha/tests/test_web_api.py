"""
Akasha Web Compiler API Tests
=============================

Tests the web backend server logic: /api/run, /api/check, /api/tokens, /api/ast, /api/examples.
Run with: pytest akasha/tests/test_web_api.py -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.web.server import run_code, get_tokens, get_ast, EXAMPLES, ast_to_dict


class TestWebAPIExecution:
    def test_run_hello_world(self):
        res = run_code('cheppu("Namaste from Web API!")')
        assert res["success"] is True
        assert "Namaste from Web API!" in res["output"]
        assert res["execution_time_ms"] >= 0

    def test_run_with_runtime_error(self):
        res = run_code('cheppu(1 / 0)')
        assert res["success"] is False
        assert res["error"] is not None
        assert res["error"]["phase"] == "Runtime"

    def test_run_with_syntax_error(self):
        res = run_code('okavela {')
        assert res["success"] is False
        assert res["error"]["phase"] in ("Parser", "Lexer")

    def test_run_complex_algorithm(self):
        code = """
karyam factorial(n) {
    okavela n <= 1 { phalitham 1 }
    phalitham n * factorial(n - 1)
}
cheppu(factorial(6))
"""
        res = run_code(code)
        assert res["success"] is True
        assert "720" in res["output"]


class TestWebAPITokens:
    def test_get_tokens_basic(self):
        res = get_tokens('viluva x = 42')
        assert res["success"] is True
        tokens = res["tokens"]
        kinds = [t["kind"] for t in tokens]
        assert "VILUVA" in kinds
        assert "IDENT" in kinds
        assert "EQ" in kinds
        assert "INTEGER" in kinds

    def test_get_tokens_error(self):
        res = get_tokens('"unterminated string')
        assert res["success"] is False
        assert "error" in res


class TestWebAPIAST:
    def test_get_ast_basic(self):
        res = get_ast('viluva x = 10 + 20')
        assert res["success"] is True
        ast = res["ast"]
        assert ast["_type"] == "Program"
        assert len(ast["body"]) == 1
        stmt = ast["body"][0]
        assert stmt["_type"] == "VarDecl"
        assert stmt["name"] == "x"
        assert stmt["value"]["_type"] == "BinaryOp"
        assert stmt["value"]["operator"] == "+"

    def test_get_ast_error(self):
        res = get_ast('karyam () {}')
        assert res["success"] is False


class TestWebAPIExamples:
    def test_examples_catalogue_validity(self):
        assert len(EXAMPLES) >= 5
        for ex in EXAMPLES:
            assert "id" in ex
            assert "title" in ex
            assert "code" in ex
            # Verify each example parses and runs without error!
            res = run_code(ex["code"])
            assert res["success"] is True, f"Example '{ex['title']}' failed: {res.get('error')}"
