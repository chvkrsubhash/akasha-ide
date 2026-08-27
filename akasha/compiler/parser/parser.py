"""
Akasha Programming Language — Recursive-Descent Parser
=====================================================

Consumes a flat list of Tokens and produces an AST (Program node).

Design:
- Recursive descent — each grammar rule becomes a method
- One-token lookahead
- Clear error messages with source location and suggestions
- No external dependencies

Grammar summary (see language_spec.md for full EBNF):
  program     ::= statement* EOF
  statement   ::= var_decl | const_decl | if | while | for | loop |
                  match | function | return | break | continue |
                  import | export | struct | unsafe | expr_stmt
  expression  ::= assignment | logical_or | ...  (Pratt-style precedence)
"""

from __future__ import annotations
from typing import Optional
from ..lexer.token import Token, TokenKind
from ..ast_nodes.nodes import (
    Program, Block, Node,
    # Literals
    IntLiteral, FloatLiteral, StringLiteral, FStringLiteral,
    BoolLiteral, NullLiteral,
    # Expressions
    Identifier, BinaryOp, UnaryOp, Assignment, Call, Index, Slice, IndexAssignment,
    FieldAccess, ArrayLiteral, MapLiteral, TupleLiteral, RangeExpr,
    Closure, MethodCall, StructLiteral, PropagateError,
    # Statements
    ExprStatement, VarDecl, ConstDecl, SecretDecl, Param,
    FunctionDecl, ReturnStmt, IfStmt, WhileStmt, ForEachStmt,
    LoopStmt, BreakStmt, ContinueStmt, MatchStmt, MatchArm,
    ImportStmt, ExportStmt, StructDecl, EnumDecl, TraitDecl,
    ImplBlock, UnsafeBlock,
    # Type
    TypeAnnotation,
)
import re


class ParseError(Exception):
    """Raised when the parser encounters unexpected syntax."""

    def __init__(self, message: str, token: Token, suggestion: str = "") -> None:
        self.token      = token
        self.suggestion = suggestion
        hint = f"\n  Hint: {suggestion}" if suggestion else ""
        super().__init__(
            f"\nParse Error at line {token.line}, col {token.col}:\n"
            f"  {message} (got {token.kind.name} {token.value!r}){hint}\n"
        )


class Parser:
    """
    Recursive-descent parser for the Akasha language.

    Usage:
        parser  = Parser(tokens)
        program = parser.parse()
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens  = tokens
        self._pos     = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def parse(self) -> Program:
        body: list[Node] = []
        while not self._at_end():
            stmt = self._parse_statement()
            if stmt is not None:
                body.append(stmt)
        return Program(body=body, line=1, col=1)

    # ── Token navigation ──────────────────────────────────────────────────────

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        if idx >= len(self._tokens):
            return self._tokens[-1]   # EOF
        return self._tokens[idx]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if not self._at_end():
            self._pos += 1
        return tok

    def _at_end(self) -> bool:
        return self._peek().kind == TokenKind.EOF

    def _check(self, *kinds: TokenKind) -> bool:
        return self._peek().kind in kinds

    def _match(self, *kinds: TokenKind) -> Optional[Token]:
        if self._check(*kinds):
            return self._advance()
        return None

    def _expect(self, kind: TokenKind, suggestion: str = "") -> Token:
        if self._check(kind):
            return self._advance()
        raise ParseError(
            f"Expected {kind.name}",
            self._peek(),
            suggestion
        )

    def _current_loc(self) -> tuple[int, int]:
        tok = self._peek()
        return tok.line, tok.col

    # ══════════════════════════════════════════════════════════════════════════
    # STATEMENTS
    # ══════════════════════════════════════════════════════════════════════════

    def _parse_statement(self) -> Optional[Node]:
        tok = self._peek()
        line, col = tok.line, tok.col

        kind = tok.kind

        if kind == TokenKind.VILUVA:
            return self._parse_var_decl()
        if kind == TokenKind.STHIRAM:
            return self._parse_const_decl()
        if kind == TokenKind.RAHASYAM:
            return self._parse_secret_decl()
        if kind == TokenKind.KARYAM:
            return self._parse_function_decl()
        if kind == TokenKind.ASYNCHRONOUS:
            # asynchronous karyam ...
            self._advance()
            fn = self._parse_function_decl()
            fn.is_async = True
            return fn
        if kind == TokenKind.PHALITHAM:
            return self._parse_return()
        if kind == TokenKind.OKAVELA:
            return self._parse_if()
        if kind == TokenKind.ALAA:
            return self._parse_while()
        if kind == TokenKind.PRATHI:
            return self._parse_for_each()
        if kind == TokenKind.LOOP:
            return self._parse_loop()
        if kind == TokenKind.AAPU:
            self._advance()
            return BreakStmt(line=line, col=col)
        if kind == TokenKind.KONASAGINCHU:
            self._advance()
            return ContinueStmt(line=line, col=col)
        if kind == TokenKind.TIRUGU:
            return self._parse_match()
        if kind == TokenKind.DIGUMATHI:
            return self._parse_import()
        if kind == TokenKind.EGUMATHI:
            return self._parse_export()
        if kind == TokenKind.RACHANA:
            return self._parse_struct_decl()
        if kind == TokenKind.VISHAYAM:
            return self._parse_enum_decl()
        if kind == TokenKind.NERPU:
            return self._parse_trait_decl()
        if kind == TokenKind.ADUGU:
            return self._parse_impl_block()
        if kind == TokenKind.ASURA:
            return self._parse_unsafe_block()

        # Fall through to expression statement
        return self._parse_expr_statement()

    def _parse_expr_statement(self) -> Node:
        expr = self._parse_expression()
        return ExprStatement(expr=expr, line=expr.line, col=expr.col)

    # ── Variable declarations ─────────────────────────────────────────────────

    def _parse_var_decl(self) -> VarDecl:
        tok = self._advance()   # consume 'viluva'
        mutable = True
        # optional 'maarpu' (explicit mutable)
        self._match(TokenKind.MAARPU)
        name_tok = self._expect(TokenKind.IDENT, "Expected variable name after 'viluva'")
        type_ann = self._parse_optional_type_annotation()
        self._expect(TokenKind.EQ, "Expected '=' after variable name")
        value = self._parse_expression()
        return VarDecl(name=name_tok.value, type_=type_ann, value=value,
                       mutable=mutable, line=tok.line, col=tok.col)

    def _parse_const_decl(self) -> ConstDecl:
        tok = self._advance()   # 'sthiram'
        name_tok = self._expect(TokenKind.IDENT, "Expected constant name after 'sthiram'")
        type_ann = self._parse_optional_type_annotation()
        self._expect(TokenKind.EQ, "Expected '=' after constant name")
        value = self._parse_expression()
        return ConstDecl(name=name_tok.value, type_=type_ann, value=value,
                         line=tok.line, col=tok.col)

    def _parse_secret_decl(self) -> SecretDecl:
        tok = self._advance()   # 'rahasyam'
        name_tok = self._expect(TokenKind.IDENT, "Expected secret name after 'rahasyam'")
        self._expect(TokenKind.EQ)
        value = self._parse_expression()
        return SecretDecl(name=name_tok.value, value=value, line=tok.line, col=tok.col)

    # ── Type annotation ───────────────────────────────────────────────────────

    def _parse_optional_type_annotation(self) -> Optional[TypeAnnotation]:
        if self._match(TokenKind.COLON):
            return self._parse_type()
        return None

    def _parse_type(self) -> TypeAnnotation:
        tok = self._peek()
        type_kinds = {
            TokenKind.SANKHYA, TokenKind.DASAMSAM, TokenKind.PADAM,
            TokenKind.NIJAM_TYPE, TokenKind.BYTE, TokenKind.PATRIKA,
            TokenKind.NAKSHA, TokenKind.GUMPU, TokenKind.JANTA,
            TokenKind.VIKALPA, TokenKind.IDENT,
        }
        if tok.kind not in type_kinds:
            raise ParseError("Expected type name", tok, "e.g. Sankhya, Padam, Nijam")
        self._advance()
        name = tok.value
        params: list[TypeAnnotation] = []
        if self._match(TokenKind.LBRACKET):
            params.append(self._parse_type())
            while self._match(TokenKind.COMMA):
                params.append(self._parse_type())
            self._expect(TokenKind.RBRACKET)
        return TypeAnnotation(name=name, params=params, line=tok.line, col=tok.col)

    # ── Functions ─────────────────────────────────────────────────────────────

    def _parse_function_decl(self) -> FunctionDecl:
        tok = self._advance()   # 'karyam'
        name_tok = self._expect(TokenKind.IDENT, "Expected function name after 'karyam'")
        self._expect(TokenKind.LPAREN)
        params = self._parse_param_list()
        self._expect(TokenKind.RPAREN)
        ret = None
        if self._match(TokenKind.COLON):
            ret = self._parse_type()
        elif self._match(TokenKind.THIN_ARROW):
            ret = self._parse_type()
        body = self._parse_block()
        return FunctionDecl(name=name_tok.value, params=params, return_type=ret,
                            body=body, is_async=False, line=tok.line, col=tok.col)

    def _parse_param_list(self) -> list[Param]:
        params: list[Param] = []
        if self._check(TokenKind.RPAREN):
            return params
        params.append(self._parse_param())
        while self._match(TokenKind.COMMA):
            if self._check(TokenKind.RPAREN):
                break
            params.append(self._parse_param())
        return params

    def _parse_param(self) -> Param:
        tok = self._peek()
        name_tok = self._expect(TokenKind.IDENT, "Expected parameter name")
        type_ann = self._parse_optional_type_annotation()
        default  = None
        if self._match(TokenKind.EQ):
            default = self._parse_expression()
        return Param(name=name_tok.value, type_=type_ann, default=default,
                     line=tok.line, col=tok.col)

    def _parse_return(self) -> ReturnStmt:
        tok = self._advance()   # 'phalitham'
        # Check if there's an expression following on the same token
        value = None
        if not self._at_end() and not self._check(TokenKind.RBRACE):
            value = self._parse_expression()
        return ReturnStmt(value=value, line=tok.line, col=tok.col)

    # ── Block ─────────────────────────────────────────────────────────────────

    def _parse_block(self) -> Block:
        tok = self._expect(TokenKind.LBRACE, "Expected '{' to start block")
        body: list[Node] = []
        while not self._check(TokenKind.RBRACE) and not self._at_end():
            stmt = self._parse_statement()
            if stmt is not None:
                body.append(stmt)
        self._expect(TokenKind.RBRACE, "Expected '}' to close block")
        return Block(body=body, line=tok.line, col=tok.col)

    # ── Control flow ──────────────────────────────────────────────────────────

    def _parse_if(self) -> IfStmt:
        tok = self._advance()   # 'okavela'
        cond = self._parse_expression()
        then = self._parse_block()
        elif_arms: list[tuple[Node, Block]] = []
        else_block: Optional[Block] = None

        while self._check(TokenKind.MARIYU):
            self._advance()
            elif_cond  = self._parse_expression()
            elif_block = self._parse_block()
            elif_arms.append((elif_cond, elif_block))

        if self._match(TokenKind.LEKAPOTHE):
            else_block = self._parse_block()

        return IfStmt(condition=cond, then_block=then, elif_arms=elif_arms,
                      else_block=else_block, line=tok.line, col=tok.col)

    def _parse_while(self) -> WhileStmt:
        tok = self._advance()   # 'alaa'
        cond = self._parse_expression()
        body = self._parse_block()
        return WhileStmt(condition=cond, body=body, line=tok.line, col=tok.col)

    def _parse_for_each(self) -> ForEachStmt:
        tok = self._advance()   # 'prathi'
        var_tok = self._expect(TokenKind.IDENT, "Expected loop variable after 'prathi'")
        self._expect(TokenKind.LO, "Expected 'lo' after loop variable name (e.g. prathi x lo list)")
        iterable = self._parse_expression()
        body = self._parse_block()
        return ForEachStmt(var=var_tok.value, iterable=iterable,
                           body=body, line=tok.line, col=tok.col)

    def _parse_loop(self) -> LoopStmt:
        tok = self._advance()   # 'loop'
        body = self._parse_block()
        return LoopStmt(body=body, line=tok.line, col=tok.col)

    def _parse_match(self) -> MatchStmt:
        tok = self._advance()   # 'tirugu'
        subject = self._parse_expression()
        self._expect(TokenKind.LBRACE)
        arms: list[MatchArm] = []
        default_body: Optional[Node] = None

        while not self._check(TokenKind.RBRACE) and not self._at_end():
            if self._match(TokenKind.DEFAULT):
                self._expect(TokenKind.ARROW)
                if self._check(TokenKind.LBRACE):
                    default_body = self._parse_block()
                else:
                    default_body = self._parse_expression()
            elif self._check(TokenKind.STHITHI):
                self._advance()   # consume 'sthithi'
                pattern = self._parse_expression()
                self._expect(TokenKind.ARROW)
                if self._check(TokenKind.LBRACE):
                    arm_body: Node = self._parse_block()
                else:
                    arm_body = self._parse_expression()
                arms.append(MatchArm(pattern=pattern, body=arm_body,
                                     line=pattern.line, col=pattern.col))
            else:
                raise ParseError("Expected 'sthithi' or 'default' in match block", self._peek())

        self._expect(TokenKind.RBRACE)
        return MatchStmt(subject=subject, arms=arms, default=default_body,
                         line=tok.line, col=tok.col)

    # ── Modules ───────────────────────────────────────────────────────────────

    def _parse_import(self) -> ImportStmt:
        tok = self._advance()   # 'digumathi'
        module_tok = self._expect(TokenKind.IDENT, "Expected module name after 'digumathi'")
        name = None
        if self._match(TokenKind.VETHUKU):
            name_tok = self._expect(TokenKind.IDENT)
            name = name_tok.value
        return ImportStmt(module=module_tok.value, name=name, line=tok.line, col=tok.col)

    def _parse_export(self) -> ExportStmt:
        tok = self._advance()   # 'egumathi'
        decl = self._parse_statement()
        return ExportStmt(decl=decl, line=tok.line, col=tok.col)

    # ── Struct, Enum, Trait, Impl ──────────────────────────────────────────────

    def _parse_struct_decl(self) -> StructDecl:
        tok = self._advance()   # 'rachana'
        name_tok = self._expect(TokenKind.IDENT)
        self._expect(TokenKind.LBRACE)
        fields: list[tuple[str, TypeAnnotation]] = []
        while not self._check(TokenKind.RBRACE) and not self._at_end():
            field_name = self._expect(TokenKind.IDENT)
            self._expect(TokenKind.COLON)
            field_type = self._parse_type()
            self._match(TokenKind.COMMA)
            fields.append((field_name.value, field_type))
        self._expect(TokenKind.RBRACE)
        return StructDecl(name=name_tok.value, fields=fields, line=tok.line, col=tok.col)

    def _parse_enum_decl(self) -> EnumDecl:
        tok = self._advance()   # 'vishayam'
        name_tok = self._expect(TokenKind.IDENT)
        self._expect(TokenKind.LBRACE)
        variants: list[tuple[str, Optional[list[TypeAnnotation]]]] = []
        while not self._check(TokenKind.RBRACE) and not self._at_end():
            var_name = self._expect(TokenKind.IDENT)
            type_params = None
            if self._match(TokenKind.LPAREN):
                type_params = [self._parse_type()]
                while self._match(TokenKind.COMMA):
                    type_params.append(self._parse_type())
                self._expect(TokenKind.RPAREN)
            self._match(TokenKind.COMMA)
            variants.append((var_name.value, type_params))
        self._expect(TokenKind.RBRACE)
        return EnumDecl(name=name_tok.value, variants=variants, line=tok.line, col=tok.col)

    def _parse_trait_decl(self) -> TraitDecl:
        tok = self._advance()   # 'nerpu'
        name_tok = self._expect(TokenKind.IDENT)
        self._expect(TokenKind.LBRACE)
        methods: list[FunctionDecl] = []
        while not self._check(TokenKind.RBRACE) and not self._at_end():
            if self._check(TokenKind.KARYAM):
                methods.append(self._parse_function_decl())
        self._expect(TokenKind.RBRACE)
        return TraitDecl(name=name_tok.value, methods=methods, line=tok.line, col=tok.col)

    def _parse_impl_block(self) -> ImplBlock:
        tok = self._advance()   # 'adugu'
        type_name_tok = self._expect(TokenKind.IDENT)
        trait_name = None
        if self._match(TokenKind.NERPU):
            trait_name = self._expect(TokenKind.IDENT).value
        self._expect(TokenKind.LBRACE)
        methods: list[FunctionDecl] = []
        while not self._check(TokenKind.RBRACE) and not self._at_end():
            if self._check(TokenKind.KARYAM):
                methods.append(self._parse_function_decl())
        self._expect(TokenKind.RBRACE)
        return ImplBlock(type_name=type_name_tok.value, trait_name=trait_name,
                         methods=methods, line=tok.line, col=tok.col)

    def _parse_unsafe_block(self) -> UnsafeBlock:
        tok = self._advance()   # 'asura'
        body = self._parse_block()
        return UnsafeBlock(body=body, line=tok.line, col=tok.col)

    # ══════════════════════════════════════════════════════════════════════════
    # EXPRESSIONS  (Pratt-style precedence climbing)
    # ══════════════════════════════════════════════════════════════════════════

    def _parse_expression(self) -> Node:
        return self._parse_assignment()

    def _parse_assignment(self) -> Node:
        """Handle:  name = expr   or   obj[idx] = expr"""
        left = self._parse_logical_or()

        if self._check(TokenKind.EQ):
            tok = self._advance()   # '='
            right = self._parse_assignment()   # right-associative
            if isinstance(left, Identifier):
                return Assignment(name=left.name, value=right, line=tok.line, col=tok.col)
            if isinstance(left, Index):
                return IndexAssignment(obj=left.obj, index=left.index, value=right,
                                       line=tok.line, col=tok.col)
            # Fallback: assignment to arbitrary lvalue (will fail at runtime)
            return Assignment(name=str(left), value=right, line=tok.line, col=tok.col)

        return left

    def _parse_logical_or(self) -> Node:
        left = self._parse_logical_and()
        while self._check(TokenKind.OR_OR):
            op = self._advance()
            right = self._parse_logical_and()
            left = BinaryOp(left=left, operator="||", right=right,
                            line=op.line, col=op.col)
        return left

    def _parse_logical_and(self) -> Node:
        left = self._parse_equality()
        while self._check(TokenKind.AND_AND):
            op = self._advance()
            right = self._parse_equality()
            left = BinaryOp(left=left, operator="&&", right=right,
                            line=op.line, col=op.col)
        return left

    def _parse_equality(self) -> Node:
        left = self._parse_range()
        while self._check(TokenKind.EQ_EQ, TokenKind.BANG_EQ):
            op = self._advance()
            right = self._parse_range()
            left = BinaryOp(left=left, operator=op.value, right=right,
                            line=op.line, col=op.col)
        return left

    def _parse_range(self) -> Node:
        """Handle: start..end  (range literal, lower precedence than comparison)"""
        left = self._parse_comparison()
        if self._check(TokenKind.DOT_DOT):
            op  = self._advance()
            right = self._parse_comparison()
            return BinaryOp(left=left, operator="..", right=right,
                            line=op.line, col=op.col)
        return left

    def _parse_comparison(self) -> Node:
        left = self._parse_term()
        while self._check(TokenKind.LT, TokenKind.LT_EQ,
                           TokenKind.GT, TokenKind.GT_EQ):
            op = self._advance()
            right = self._parse_term()
            left = BinaryOp(left=left, operator=op.value, right=right,
                            line=op.line, col=op.col)
        return left

    def _parse_term(self) -> Node:
        left = self._parse_factor()
        while self._check(TokenKind.PLUS, TokenKind.MINUS):
            op = self._advance()
            right = self._parse_factor()
            left = BinaryOp(left=left, operator=op.value, right=right,
                            line=op.line, col=op.col)
        return left

    def _parse_factor(self) -> Node:
        left = self._parse_unary()
        while self._check(TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT):
            op = self._advance()
            right = self._parse_unary()
            left = BinaryOp(left=left, operator=op.value, right=right,
                            line=op.line, col=op.col)
        return left

    def _parse_unary(self) -> Node:
        if self._check(TokenKind.BANG, TokenKind.MINUS):
            op  = self._advance()
            rhs = self._parse_unary()
            return UnaryOp(operator=op.value, operand=rhs,
                           line=op.line, col=op.col)
        return self._parse_power()

    def _parse_power(self) -> Node:
        base = self._parse_postfix()
        if self._check(TokenKind.STAR_STAR):
            op  = self._advance()
            exp = self._parse_unary()   # right-associative
            return BinaryOp(left=base, operator="**", right=exp,
                            line=op.line, col=op.col)
        return base

    def _parse_postfix(self) -> Node:
        """Handles: call(), indexing[], .field, .method(), ? propagation"""
        node = self._parse_primary()

        while True:
            if self._check(TokenKind.LPAREN):
                # Call: expr(args)
                tok = self._advance()
                args = self._parse_arg_list()
                self._expect(TokenKind.RPAREN)
                node = Call(callee=node, arguments=args,
                            line=tok.line, col=tok.col)

            elif self._check(TokenKind.LBRACKET):
                # Index or slice: expr[idx] or expr[a..b]
                tok = self._advance()
                idx = self._parse_expression()
                if self._check(TokenKind.DOT_DOT):
                    self._advance()
                    end = self._parse_expression()
                    self._expect(TokenKind.RBRACKET)
                    node = Slice(obj=node, start=idx, end=end,
                                 line=tok.line, col=tok.col)
                else:
                    self._expect(TokenKind.RBRACKET)
                    node = Index(obj=node, index=idx,
                                 line=tok.line, col=tok.col)

            elif self._check(TokenKind.DOT):
                tok = self._advance()
                field_tok = self._expect(TokenKind.IDENT)
                if self._check(TokenKind.LPAREN):
                    # Method call: obj.method(args)
                    self._advance()
                    args = self._parse_arg_list()
                    self._expect(TokenKind.RPAREN)
                    node = MethodCall(obj=node, method=field_tok.value, args=args,
                                      line=tok.line, col=tok.col)
                else:
                    # Field access: obj.field
                    node = FieldAccess(obj=node, field=field_tok.value,
                                       line=tok.line, col=tok.col)

            elif self._check(TokenKind.QUESTION):
                tok = self._advance()
                node = PropagateError(expr=node, line=tok.line, col=tok.col)

            else:
                break

        return node

    def _parse_primary(self) -> Node:
        tok = self._peek()

        # Literals
        if tok.kind == TokenKind.INTEGER:
            self._advance()
            raw = tok.value.replace("_", "")
            val = int(raw, 16) if raw.startswith("0x") or raw.startswith("0X") else int(raw)
            return IntLiteral(value=val, line=tok.line, col=tok.col)

        if tok.kind == TokenKind.FLOAT:
            self._advance()
            return FloatLiteral(value=float(tok.value.replace("_", "")),
                                line=tok.line, col=tok.col)

        if tok.kind == TokenKind.STRING:
            self._advance()
            return StringLiteral(value=tok.value, line=tok.line, col=tok.col)

        if tok.kind == TokenKind.FSTRING:
            self._advance()
            parts = self._parse_fstring_parts(tok.value, tok.line, tok.col)
            return FStringLiteral(parts=parts, line=tok.line, col=tok.col)

        if tok.kind == TokenKind.BOOL_TRUE:
            self._advance()
            return BoolLiteral(value=True, line=tok.line, col=tok.col)

        if tok.kind == TokenKind.BOOL_FALSE:
            self._advance()
            return BoolLiteral(value=False, line=tok.line, col=tok.col)

        if tok.kind == TokenKind.NULL:
            self._advance()
            return NullLiteral(line=tok.line, col=tok.col)

        # Grouped expression or tuple
        if tok.kind == TokenKind.LPAREN:
            return self._parse_grouped_or_tuple()

        # Array literal
        if tok.kind == TokenKind.LBRACKET:
            return self._parse_array_literal()

        # Map literal
        if tok.kind == TokenKind.LBRACE:
            return self._parse_map_literal()

        # Closure:  muppu(params) => expr
        if tok.kind == TokenKind.MUPPU:
            return self._parse_closure()

        # Range shorthand starting with integer (0..10 parsed as RangeExpr
        # when not inside a for loop — handled via BinaryOp with DOT_DOT)

        # Identifier or struct literal
        if tok.kind == TokenKind.IDENT:
            self._advance()
            ident = Identifier(name=tok.value, line=tok.line, col=tok.col)
            # Struct literal: TypeName { field: expr, ... }
            if self._check(TokenKind.LBRACE):
                # Peek ahead: if next-next is IDENT COLON, it's a struct literal
                if self._peek(1).kind == TokenKind.IDENT and self._peek(2).kind == TokenKind.COLON:
                    return self._parse_struct_literal(tok)
            return ident

        # Type names used as conversion functions: Sankhya(x), Padam(x), Dasamsam(x)
        _type_callable_kinds = {
            TokenKind.SANKHYA, TokenKind.DASAMSAM, TokenKind.PADAM,
            TokenKind.NIJAM_TYPE, TokenKind.BYTE, TokenKind.PATRIKA,
            TokenKind.NAKSHA, TokenKind.GUMPU, TokenKind.JANTA,
            TokenKind.VIKALPA,
        }
        if tok.kind in _type_callable_kinds:
            self._advance()
            return Identifier(name=tok.value, line=tok.line, col=tok.col)

        raise ParseError(
            f"Unexpected token in expression",

            tok,
            "Expected a value, variable name, or expression"
        )

    def _parse_grouped_or_tuple(self) -> Node:
        tok = self._advance()   # '('
        if self._check(TokenKind.RPAREN):
            self._advance()
            return TupleLiteral(elements=[], line=tok.line, col=tok.col)

        first = self._parse_expression()
        if self._match(TokenKind.COMMA):
            # Tuple
            elements = [first]
            while not self._check(TokenKind.RPAREN) and not self._at_end():
                elements.append(self._parse_expression())
                if not self._match(TokenKind.COMMA):
                    break
            self._expect(TokenKind.RPAREN)
            return TupleLiteral(elements=elements, line=tok.line, col=tok.col)
        self._expect(TokenKind.RPAREN)
        return first

    def _parse_array_literal(self) -> ArrayLiteral:
        tok = self._advance()   # '['
        elements: list[Node] = []
        if not self._check(TokenKind.RBRACKET):
            elements.append(self._parse_expression())
            while self._match(TokenKind.COMMA):
                if self._check(TokenKind.RBRACKET):
                    break
                elements.append(self._parse_expression())
        self._expect(TokenKind.RBRACKET)
        return ArrayLiteral(elements=elements, line=tok.line, col=tok.col)

    def _parse_map_literal(self) -> MapLiteral:
        tok = self._advance()   # '{'
        pairs: list[tuple[Node, Node]] = []
        while not self._check(TokenKind.RBRACE) and not self._at_end():
            key = self._parse_expression()
            self._expect(TokenKind.COLON)
            val = self._parse_expression()
            pairs.append((key, val))
            if not self._match(TokenKind.COMMA):
                break
        self._expect(TokenKind.RBRACE)
        return MapLiteral(pairs=pairs, line=tok.line, col=tok.col)

    def _parse_struct_literal(self, name_tok: Token) -> StructLiteral:
        self._advance()   # '{'
        fields: list[tuple[str, Node]] = []
        while not self._check(TokenKind.RBRACE) and not self._at_end():
            field_tok = self._expect(TokenKind.IDENT)
            self._expect(TokenKind.COLON)
            val = self._parse_expression()
            fields.append((field_tok.value, val))
            if not self._match(TokenKind.COMMA):
                break
        self._expect(TokenKind.RBRACE)
        return StructLiteral(name=name_tok.value, fields=fields,
                             line=name_tok.line, col=name_tok.col)

    def _parse_closure(self) -> Closure:
        tok = self._advance()   # 'muppu'
        self._expect(TokenKind.LPAREN)
        params = self._parse_param_list()
        self._expect(TokenKind.RPAREN)
        self._expect(TokenKind.ARROW, "Expected '=>' after closure parameters")
        if self._check(TokenKind.LBRACE):
            body: Node = self._parse_block()
        else:
            body = self._parse_expression()
        return Closure(params=params, body=body, line=tok.line, col=tok.col)

    def _parse_arg_list(self) -> list[Node]:
        args: list[Node] = []
        if self._check(TokenKind.RPAREN):
            return args
        args.append(self._parse_expression())
        while self._match(TokenKind.COMMA):
            if self._check(TokenKind.RPAREN):
                break
            args.append(self._parse_expression())
        return args

    # ── F-string interpolation ────────────────────────────────────────────────

    def _parse_fstring_parts(self, raw: str, line: int, col: int) -> list[str | Node]:
        """
        Split f-string raw text into literal strings and embedded expressions.
        e.g. "Hello, {peru}!" → ["Hello, ", Identifier("peru"), "!"]
        """
        parts: list[str | Node] = []
        i = 0
        buf: list[str] = []
        while i < len(raw):
            if raw[i] == "{":
                if buf:
                    parts.append("".join(buf))
                    buf = []
                # find matching '}'
                depth = 1
                i += 1
                expr_buf: list[str] = []
                while i < len(raw) and depth > 0:
                    if raw[i] == "{":
                        depth += 1
                    elif raw[i] == "}":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    expr_buf.append(raw[i])
                    i += 1
                expr_src = "".join(expr_buf).strip()
                # Re-lex and parse the interpolated expression
                from ..lexer.lexer import Lexer as _Lexer
                inner_tokens = _Lexer(expr_src, "<fstring>").tokenize()
                inner_parser = Parser(inner_tokens)
                expr_node = inner_parser._parse_expression()
                parts.append(expr_node)
            else:
                buf.append(raw[i])
                i += 1
        if buf:
            parts.append("".join(buf))
        return parts
