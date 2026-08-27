"""
Akasha Programming Language — Lexer
==================================

Transforms raw source text into a flat list of Tokens.

Design:
- Single-pass, character-by-character
- Tracks line/col for all tokens (precise error messages)
- Supports: keywords, identifiers, integer/float literals,
  single/double-quoted strings, f-strings, comments (-- and --- ... ---),
  all operators, delimiters
- No external dependencies
"""

from __future__ import annotations
from typing import List
from .token import Token, TokenKind, KEYWORDS


class LexerError(Exception):
    """Raised when the lexer encounters an illegal character or unterminated token."""

    def __init__(self, message: str, line: int, col: int) -> None:
        self.line = line
        self.col  = col
        super().__init__(
            f"\nLexer Error at line {line}, col {col}:\n"
            f"  {message}\n"
        )


class Lexer:
    """
    Converts a Akasha source string into a list of Tokens.

    Usage:
        lexer  = Lexer(source, filename="hello.akasha")
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str, filename: str = "<stdin>") -> None:
        self._src      = source
        self._filename = filename
        self._pos      = 0          # current character index
        self._line     = 1
        self._col      = 1
        self._tokens: List[Token] = []

    # ── Public API ───────────────────────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        """Lex the entire source and return all tokens (including EOF)."""
        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break
            tok = self._next_token()
            if tok is not None:
                self._tokens.append(tok)

        self._tokens.append(Token(TokenKind.EOF, "", self._line, self._col))
        return self._tokens

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._src[idx] if idx < len(self._src) else "\0"

    def _advance(self) -> str:
        ch = self._src[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _at_end(self) -> bool:
        return self._pos >= len(self._src)

    def _match(self, expected: str) -> bool:
        """Consume next char if it matches expected."""
        if self._at_end():
            return False
        if self._src[self._pos] == expected:
            self._advance()
            return True
        return False

    def _make_token(self, kind: TokenKind, value: str, line: int, col: int) -> Token:
        return Token(kind, value, line, col)

    # ── Whitespace & Comments ────────────────────────────────────────────────

    def _skip_whitespace_and_comments(self) -> None:
        while not self._at_end():
            ch = self._peek()

            # Whitespace (spaces, tabs, carriage returns, newlines)
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()

            # Multi-line comment: --- ... ---
            elif ch == "-" and self._peek(1) == "-" and self._peek(2) == "-":
                self._advance(); self._advance(); self._advance()  # consume ---
                while not self._at_end():
                    if self._peek() == "-" and self._peek(1) == "-" and self._peek(2) == "-":
                        self._advance(); self._advance(); self._advance()
                        break
                    self._advance()

            # Single-line comment: -- ...
            elif ch == "-" and self._peek(1) == "-":
                while not self._at_end() and self._peek() != "\n":
                    self._advance()

            else:
                break

    # ── Main dispatch ────────────────────────────────────────────────────────

    def _next_token(self) -> Token | None:
        line = self._line
        col  = self._col
        ch   = self._advance()

        # ── String literals ───────────────────────────────────────────────
        if ch == "f" and self._peek() in ('"', "'"):
            return self._lex_fstring(line, col)

        if ch in ('"', "'"):
            return self._lex_string(ch, line, col)

        # ── Numbers ───────────────────────────────────────────────────────
        if ch.isdigit() or (ch == "0" and self._peek() in ("x", "X")):
            return self._lex_number(ch, line, col)

        # ── Identifiers & Keywords ────────────────────────────────────────
        if ch.isalpha() or ch == "_":
            return self._lex_ident_or_keyword(ch, line, col)

        # ── Operators & Delimiters ────────────────────────────────────────
        return self._lex_operator(ch, line, col)

    # ── String lexing ────────────────────────────────────────────────────────

    def _lex_string(self, quote: str, line: int, col: int) -> Token:
        buf: list[str] = []
        while not self._at_end():
            ch = self._advance()
            if ch == quote:
                return self._make_token(TokenKind.STRING, "".join(buf), line, col)
            if ch == "\\":
                buf.append(self._lex_escape())
            elif ch == "\n":
                raise LexerError("Unterminated string literal", self._line, self._col)
            else:
                buf.append(ch)
        raise LexerError("Unterminated string literal (reached end of file)", line, col)

    def _lex_fstring(self, line: int, col: int) -> Token:
        """Lex f"..." — stored as raw text; interpolation handled in parser."""
        quote = self._advance()   # consume the opening " or '
        buf: list[str] = []
        depth = 0
        while not self._at_end():
            ch = self._advance()
            if ch == "{":
                depth += 1
                buf.append(ch)
            elif ch == "}":
                depth -= 1
                buf.append(ch)
            elif ch == quote and depth == 0:
                return self._make_token(TokenKind.FSTRING, "".join(buf), line, col)
            elif ch == "\\":
                buf.append("\\")
                buf.append(self._advance())
            else:
                buf.append(ch)
        raise LexerError("Unterminated f-string", line, col)

    def _lex_escape(self) -> str:
        if self._at_end():
            raise LexerError("Unexpected end of escape sequence", self._line, self._col)
        ch = self._advance()
        escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\",
                   '"': '"', "'": "'", "0": "\0"}
        if ch in escapes:
            return escapes[ch]
        raise LexerError(f"Unknown escape sequence '\\{ch}'", self._line, self._col)

    # ── Number lexing ────────────────────────────────────────────────────────

    def _lex_number(self, first: str, line: int, col: int) -> Token:
        buf = [first]

        # Hex literal: 0x...
        if first == "0" and self._peek() in ("x", "X"):
            buf.append(self._advance())  # 'x'
            while self._peek().isdigit() or self._peek().lower() in "abcdef":
                buf.append(self._advance())
            return self._make_token(TokenKind.INTEGER, "".join(buf), line, col)

        # Decimal integer or float
        while self._peek().isdigit() or self._peek() == "_":
            buf.append(self._advance())

        # Float
        if self._peek() == "." and self._peek(1).isdigit():
            buf.append(self._advance())  # '.'
            while self._peek().isdigit() or self._peek() == "_":
                buf.append(self._advance())
            # Scientific notation
            if self._peek() in ("e", "E"):
                buf.append(self._advance())
                if self._peek() in ("+", "-"):
                    buf.append(self._advance())
                while self._peek().isdigit():
                    buf.append(self._advance())
            return self._make_token(TokenKind.FLOAT, "".join(buf), line, col)

        return self._make_token(TokenKind.INTEGER, "".join(buf), line, col)

    # ── Identifier & Keyword ─────────────────────────────────────────────────

    def _lex_ident_or_keyword(self, first: str, line: int, col: int) -> Token:
        buf = [first]
        while self._peek().isalnum() or self._peek() == "_":
            buf.append(self._advance())
        word = "".join(buf)

        # Check reserved keywords
        if word in KEYWORDS:
            return self._make_token(KEYWORDS[word], word, line, col)

        return self._make_token(TokenKind.IDENT, word, line, col)

    # ── Operators & Delimiters ───────────────────────────────────────────────

    def _lex_operator(self, ch: str, line: int, col: int) -> Token:
        def tok(kind: TokenKind, val: str) -> Token:
            return self._make_token(kind, val, line, col)

        match ch:
            case "(": return tok(TokenKind.LPAREN,    "(")
            case ")": return tok(TokenKind.RPAREN,    ")")
            case "{": return tok(TokenKind.LBRACE,    "{")
            case "}": return tok(TokenKind.RBRACE,    "}")
            case "[": return tok(TokenKind.LBRACKET,  "[")
            case "]": return tok(TokenKind.RBRACKET,  "]")
            case ",": return tok(TokenKind.COMMA,     ",")
            case ":": return tok(TokenKind.COLON,     ":")
            case ";": return tok(TokenKind.SEMICOLON, ";")
            case "%": return tok(TokenKind.PERCENT,   "%")
            case "?": return tok(TokenKind.QUESTION,  "?")
            case "&":
                if self._match("&"):
                    return tok(TokenKind.AND_AND, "&&")
                return tok(TokenKind.AMP, "&")
            case "|":
                if self._match("|"):
                    return tok(TokenKind.OR_OR, "||")
                raise LexerError(f"Unexpected character '|'. Did you mean '||'?", line, col)
            case "+": return tok(TokenKind.PLUS,  "+")
            case "-":
                if self._match(">"):
                    return tok(TokenKind.THIN_ARROW, "->")
                # Note: '--' comments handled in skip_whitespace, so '-' alone is MINUS
                return tok(TokenKind.MINUS, "-")
            case "*":
                if self._match("*"):
                    return tok(TokenKind.STAR_STAR, "**")
                return tok(TokenKind.STAR, "*")
            case "/": return tok(TokenKind.SLASH, "/")
            case "!":
                if self._match("="):
                    return tok(TokenKind.BANG_EQ, "!=")
                return tok(TokenKind.BANG, "!")
            case "=":
                if self._match("="):
                    return tok(TokenKind.EQ_EQ, "==")
                if self._match(">"):
                    return tok(TokenKind.ARROW, "=>")
                return tok(TokenKind.EQ, "=")
            case "<":
                if self._match("="):
                    return tok(TokenKind.LT_EQ, "<=")
                return tok(TokenKind.LT, "<")
            case ">":
                if self._match("="):
                    return tok(TokenKind.GT_EQ, ">=")
                return tok(TokenKind.GT, ">")
            case ".":
                if self._match("."):
                    return tok(TokenKind.DOT_DOT, "..")
                return tok(TokenKind.DOT, ".")
            case _:
                raise LexerError(
                    f"Unexpected character {ch!r}",
                    line, col
                )
