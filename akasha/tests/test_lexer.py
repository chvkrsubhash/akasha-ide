"""
Akasha Lexer Tests
================

Tests every token type produced by the Akasha lexer.
Run with: pytest tests/test_lexer.py -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.compiler.lexer.lexer import Lexer, LexerError
from akasha.compiler.lexer.token import TokenKind


def lex(source: str):
    """Helper: tokenize source, strip EOF token."""
    tokens = Lexer(source).tokenize()
    return [t for t in tokens if t.kind != TokenKind.EOF]


def kinds(source: str) -> list[TokenKind]:
    return [t.kind for t in lex(source)]


def values(source: str) -> list[str]:
    return [t.value for t in lex(source)]


# ── Integer Literals ──────────────────────────────────────────────────────────

class TestIntegerLiterals:
    def test_simple_integer(self):
        toks = lex("42")
        assert len(toks) == 1
        assert toks[0].kind == TokenKind.INTEGER
        assert toks[0].value == "42"

    def test_zero(self):
        toks = lex("0")
        assert toks[0].kind == TokenKind.INTEGER
        assert toks[0].value == "0"

    def test_hex_literal(self):
        toks = lex("0xFF")
        assert toks[0].kind == TokenKind.INTEGER
        assert toks[0].value == "0xFF"

    def test_hex_uppercase(self):
        toks = lex("0XAB12")
        assert toks[0].kind == TokenKind.INTEGER

    def test_underscore_separator(self):
        toks = lex("1_000_000")
        assert toks[0].kind == TokenKind.INTEGER
        assert toks[0].value == "1_000_000"


# ── Float Literals ────────────────────────────────────────────────────────────

class TestFloatLiterals:
    def test_simple_float(self):
        toks = lex("3.14")
        assert toks[0].kind == TokenKind.FLOAT

    def test_float_no_leading_zero(self):
        # 0.5
        toks = lex("0.5")
        assert toks[0].kind == TokenKind.FLOAT

    def test_float_scientific(self):
        toks = lex("1.5e10")
        assert toks[0].kind == TokenKind.FLOAT

    def test_float_neg_exponent(self):
        toks = lex("2.0e-3")
        assert toks[0].kind == TokenKind.FLOAT


# ── String Literals ───────────────────────────────────────────────────────────

class TestStringLiterals:
    def test_double_quoted(self):
        toks = lex('"hello"')
        assert toks[0].kind == TokenKind.STRING
        assert toks[0].value == "hello"

    def test_single_quoted(self):
        toks = lex("'world'")
        assert toks[0].kind == TokenKind.STRING
        assert toks[0].value == "world"

    def test_empty_string(self):
        toks = lex('""')
        assert toks[0].kind == TokenKind.STRING
        assert toks[0].value == ""

    def test_escape_newline(self):
        toks = lex('"hello\\nworld"')
        assert toks[0].kind == TokenKind.STRING
        assert "\n" in toks[0].value

    def test_escape_tab(self):
        toks = lex('"col1\\tcol2"')
        assert "\t" in toks[0].value

    def test_unterminated_string(self):
        with pytest.raises(LexerError):
            Lexer('"unterminated').tokenize()

    def test_fstring(self):
        toks = lex('f"Hello, {name}!"')
        assert toks[0].kind == TokenKind.FSTRING
        assert "Hello, " in toks[0].value
        assert "name" in toks[0].value


# ── Keywords ──────────────────────────────────────────────────────────────────

class TestKeywords:
    def test_okavela(self):
        assert kinds("okavela") == [TokenKind.OKAVELA]

    def test_lekapothe(self):
        assert kinds("lekapothe") == [TokenKind.LEKAPOTHE]

    def test_mariyu(self):
        assert kinds("mariyu") == [TokenKind.MARIYU]

    def test_alaa(self):
        assert kinds("alaa") == [TokenKind.ALAA]

    def test_prathi(self):
        assert kinds("prathi") == [TokenKind.PRATHI]

    def test_loop(self):
        assert kinds("loop") == [TokenKind.LOOP]

    def test_aapu(self):
        assert kinds("aapu") == [TokenKind.AAPU]

    def test_konasaginchu(self):
        assert kinds("konasaginchu") == [TokenKind.KONASAGINCHU]

    def test_karyam(self):
        assert kinds("karyam") == [TokenKind.KARYAM]

    def test_phalitham(self):
        assert kinds("phalitham") == [TokenKind.PHALITHAM]

    def test_viluva(self):
        assert kinds("viluva") == [TokenKind.VILUVA]

    def test_sthiram(self):
        assert kinds("sthiram") == [TokenKind.STHIRAM]

    def test_nijam(self):
        assert kinds("nijam") == [TokenKind.BOOL_TRUE]

    def test_abaddham(self):
        assert kinds("abaddham") == [TokenKind.BOOL_FALSE]

    def test_shunyam(self):
        assert kinds("shunyam") == [TokenKind.NULL]

    def test_lo(self):
        assert kinds("lo") == [TokenKind.LO]

    def test_tirugu(self):
        assert kinds("tirugu") == [TokenKind.TIRUGU]

    def test_sthithi(self):
        assert kinds("sthithi") == [TokenKind.STHITHI]

    def test_muppu(self):
        assert kinds("muppu") == [TokenKind.MUPPU]

    def test_digumathi(self):
        assert kinds("digumathi") == [TokenKind.DIGUMATHI]

    def test_rachana(self):
        assert kinds("rachana") == [TokenKind.RACHANA]


# ── Identifiers ───────────────────────────────────────────────────────────────

class TestIdentifiers:
    def test_simple_ident(self):
        toks = lex("myVariable")
        assert toks[0].kind == TokenKind.IDENT
        assert toks[0].value == "myVariable"

    def test_ident_with_underscore(self):
        toks = lex("my_var")
        assert toks[0].kind == TokenKind.IDENT

    def test_ident_starting_underscore(self):
        toks = lex("_private")
        assert toks[0].kind == TokenKind.IDENT

    def test_ident_with_numbers(self):
        toks = lex("var123")
        assert toks[0].kind == TokenKind.IDENT

    def test_type_names_are_keywords(self):
        assert kinds("Sankhya") == [TokenKind.SANKHYA]
        assert kinds("Padam") == [TokenKind.PADAM]


# ── Operators ─────────────────────────────────────────────────────────────────

class TestOperators:
    def test_arithmetic(self):
        assert kinds("+ - * / % **") == [
            TokenKind.PLUS, TokenKind.MINUS, TokenKind.STAR,
            TokenKind.SLASH, TokenKind.PERCENT, TokenKind.STAR_STAR
        ]

    def test_comparison(self):
        assert kinds("== != < <= > >=") == [
            TokenKind.EQ_EQ, TokenKind.BANG_EQ,
            TokenKind.LT, TokenKind.LT_EQ,
            TokenKind.GT, TokenKind.GT_EQ
        ]

    def test_logical(self):
        assert kinds("&& ||") == [TokenKind.AND_AND, TokenKind.OR_OR]

    def test_assign(self):
        assert kinds("=") == [TokenKind.EQ]

    def test_arrow(self):
        assert kinds("=>") == [TokenKind.ARROW]

    def test_thin_arrow(self):
        assert kinds("->") == [TokenKind.THIN_ARROW]

    def test_dot(self):
        assert kinds(".") == [TokenKind.DOT]

    def test_dot_dot(self):
        assert kinds("..") == [TokenKind.DOT_DOT]

    def test_bang(self):
        assert kinds("!") == [TokenKind.BANG]


# ── Delimiters ────────────────────────────────────────────────────────────────

class TestDelimiters:
    def test_parens(self):
        assert kinds("()") == [TokenKind.LPAREN, TokenKind.RPAREN]

    def test_braces(self):
        assert kinds("{}") == [TokenKind.LBRACE, TokenKind.RBRACE]

    def test_brackets(self):
        assert kinds("[]") == [TokenKind.LBRACKET, TokenKind.RBRACKET]

    def test_comma(self):
        assert kinds(",") == [TokenKind.COMMA]

    def test_colon(self):
        assert kinds(":") == [TokenKind.COLON]


# ── Comments ──────────────────────────────────────────────────────────────────

class TestComments:
    def test_single_line_comment_ignored(self):
        toks = lex("-- this is a comment")
        assert toks == []

    def test_code_after_comment_ignored(self):
        toks = lex("42 -- this is 42")
        assert len(toks) == 1
        assert toks[0].kind == TokenKind.INTEGER

    def test_multi_line_comment_ignored(self):
        toks = lex("--- this is\na multi-line\ncomment ---")
        assert toks == []

    def test_code_after_multi_comment(self):
        toks = lex("--- comment --- 42")
        assert len(toks) == 1
        assert toks[0].kind == TokenKind.INTEGER


# ── Source Location ───────────────────────────────────────────────────────────

class TestSourceLocation:
    def test_line_tracking(self):
        toks = lex("cheppu\nhello")
        assert toks[0].line == 1
        assert toks[1].line == 2

    def test_col_tracking(self):
        toks = lex("  42")
        assert toks[0].col == 3   # 1-indexed, after 2 spaces

    def test_multiline_col_reset(self):
        toks = lex("a\nb")
        assert toks[0].col == 1
        assert toks[1].col == 1


# ── Complex Tokenization ──────────────────────────────────────────────────────

class TestComplexTokenization:
    def test_hello_world(self):
        k = kinds('cheppu("Namaste!")')
        assert k[0] == TokenKind.IDENT
        assert k[1] == TokenKind.LPAREN
        assert k[2] == TokenKind.STRING
        assert k[3] == TokenKind.RPAREN

    def test_variable_declaration(self):
        k = kinds("viluva x = 42")
        assert k == [TokenKind.VILUVA, TokenKind.IDENT, TokenKind.EQ, TokenKind.INTEGER]

    def test_function_call_chain(self):
        k = kinds("obj.method()")
        assert TokenKind.DOT in k

    def test_range_expression(self):
        k = kinds("1..10")
        assert k == [TokenKind.INTEGER, TokenKind.DOT_DOT, TokenKind.INTEGER]

    def test_if_statement(self):
        k = kinds("okavela x > 0 { aapu }")
        assert k[0] == TokenKind.OKAVELA
        assert TokenKind.LBRACE in k
        assert TokenKind.AAPU in k

    def test_for_loop(self):
        source = "prathi i lo 1..5 { cheppu(i) }"
        k = kinds(source)
        assert k[0] == TokenKind.PRATHI
        assert k[2] == TokenKind.LO
