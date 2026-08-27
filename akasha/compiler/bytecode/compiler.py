"""
Akasha Bytecode Compiler (AST -> Bytecode Chunk)
================================================

Compiles an Akasha AST into a sequence of stack-based VM instructions.
"""

from __future__ import annotations
from typing import Any, Optional
from .opcodes import OpCode, Instruction, CMP_SYMBOLS
from .serializer import CodeChunk
from ..ast_nodes.nodes import (
    Node, Program, Block,
    IntLiteral, FloatLiteral, StringLiteral, FStringLiteral,
    BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, Assignment, IndexAssignment, Call, Index, Slice,
    FieldAccess, ArrayLiteral, MapLiteral, TupleLiteral, RangeExpr,
    Closure, MethodCall, StructLiteral, PropagateError,
    ExprStatement, VarDecl, ConstDecl, SecretDecl,
    FunctionDecl, ReturnStmt, IfStmt, WhileStmt, ForEachStmt,
    LoopStmt, BreakStmt, ContinueStmt, MatchStmt, MatchArm,
    ImportStmt, ExportStmt, StructDecl, EnumDecl,
    TraitDecl, ImplBlock, UnsafeBlock,
)


class BytecodeCompiler:
    """Compiles an Akasha AST into a CodeChunk."""

    def __init__(self, filename: str = "<unknown>") -> None:
        self.filename = filename
        self.chunk: CodeChunk = CodeChunk(name="<module>", filename=filename)
        # Stacks for break and continue jump patching: list of list of instruction indices
        self._break_stack: list[list[int]] = []
        self._continue_stack: list[int] = []

    def compile(self, ast: Program) -> CodeChunk:
        """Compile a Program AST node into a top-level CodeChunk."""
        self.chunk = CodeChunk(name="<module>", filename=self.filename)
        for stmt in ast.body:
            self._compile_statement(stmt)

        # Emit explicit end-of-module return
        none_idx = self.chunk.add_constant(None)
        self.chunk.emit(OpCode.LOAD_CONST, none_idx, None)
        self.chunk.emit(OpCode.RETURN_VALUE)
        return self.chunk

    # ── Statements ────────────────────────────────────────────────────────────

    def _compile_statement(self, node: Node) -> None:
        match node.__class__.__name__:
            case "ExprStatement":
                self._compile_expression(node.expr) # type: ignore
                self.chunk.emit(OpCode.POP_TOP, line=node.line, col=node.col)

            case "VarDecl" | "ConstDecl" | "SecretDecl":
                if node.value is not None: # type: ignore
                    self._compile_expression(node.value) # type: ignore
                else:
                    none_idx = self.chunk.add_constant(None)
                    self.chunk.emit(OpCode.LOAD_CONST, none_idx, None, line=node.line, col=node.col)
                name_idx = self.chunk.add_name(node.name) # type: ignore
                self.chunk.emit(OpCode.STORE_NAME, name_idx, node.name, line=node.line, col=node.col) # type: ignore

            case "FunctionDecl":
                self._compile_function_decl(node) # type: ignore

            case "ReturnStmt":
                if node.value is not None: # type: ignore
                    self._compile_expression(node.value) # type: ignore
                else:
                    none_idx = self.chunk.add_constant(None)
                    self.chunk.emit(OpCode.LOAD_CONST, none_idx, None, line=node.line, col=node.col)
                self.chunk.emit(OpCode.RETURN_VALUE, line=node.line, col=node.col)

            case "IfStmt":
                self._compile_if(node) # type: ignore

            case "WhileStmt":
                self._compile_while(node) # type: ignore

            case "LoopStmt":
                self._compile_loop(node) # type: ignore

            case "ForEachStmt":
                self._compile_for_each(node) # type: ignore

            case "BreakStmt":
                if not self._break_stack:
                    raise SyntaxError(f"'aapu' (break) outside loop at line {node.line}")
                jump_idx = self.chunk.emit(OpCode.JUMP_ABSOLUTE, 0, line=node.line, col=node.col)
                self._break_stack[-1].append(jump_idx)

            case "ContinueStmt":
                if not self._continue_stack:
                    raise SyntaxError(f"'konasaginchu' (continue) outside loop at line {node.line}")
                target = self._continue_stack[-1]
                self.chunk.emit(OpCode.JUMP_ABSOLUTE, target, line=node.line, col=node.col)

            case "MatchStmt":
                self._compile_match(node) # type: ignore

            case "Block":
                for s in node.body: # type: ignore
                    self._compile_statement(s)

            case _:
                # Fallback expression statement
                if hasattr(node, "expr"):
                    self._compile_expression(node.expr) # type: ignore
                    self.chunk.emit(OpCode.POP_TOP, line=node.line, col=node.col)

    # ── Functions ─────────────────────────────────────────────────────────────

    def _compile_function_decl(self, node: FunctionDecl) -> None:
        func_compiler = BytecodeCompiler(filename=self.filename)
        func_chunk = CodeChunk(name=node.name, filename=self.filename)
        func_chunk.argnames = [p.name for p in node.params]
        func_compiler.chunk = func_chunk

        # Compile body
        for stmt in node.body.body:
            func_compiler._compile_statement(stmt)

        # Implicit return None at end of function
        none_idx = func_chunk.add_constant(None)
        func_chunk.emit(OpCode.LOAD_CONST, none_idx, None)
        func_chunk.emit(OpCode.RETURN_VALUE)

        # Store compiled function in outer chunk's constants
        chunk_idx = self.chunk.add_constant(func_chunk)
        self.chunk.emit(OpCode.LOAD_CONST, chunk_idx, func_chunk, line=node.line, col=node.col)
        self.chunk.emit(OpCode.MAKE_FUNCTION, line=node.line, col=node.col)
        name_idx = self.chunk.add_name(node.name)
        self.chunk.emit(OpCode.STORE_NAME, name_idx, node.name, line=node.line, col=node.col)

    # ── Control Flow ──────────────────────────────────────────────────────────

    def _compile_if(self, node: IfStmt) -> None:
        # 1. Condition
        self._compile_expression(node.condition)
        jump_to_else = self.chunk.emit(OpCode.POP_JUMP_IF_FALSE, 0, line=node.line, col=node.col)

        # 2. Then block
        for stmt in node.then_block.body:
            self._compile_statement(stmt)

        jumps_to_end: list[int] = []
        if node.elif_arms or node.else_block:
            jumps_to_end.append(self.chunk.emit(OpCode.JUMP_ABSOLUTE, 0))

        # 3. Patch condition jump to next branch
        self.chunk.patch_jump(jump_to_else, len(self.chunk.instructions))

        # 4. Elif arms
        for cond, arm_block in node.elif_arms:
            self._compile_expression(cond)
            jump_next = self.chunk.emit(OpCode.POP_JUMP_IF_FALSE, 0)
            for stmt in arm_block.body:
                self._compile_statement(stmt)
            if node.else_block or len(node.elif_arms) > 1:
                jumps_to_end.append(self.chunk.emit(OpCode.JUMP_ABSOLUTE, 0))
            self.chunk.patch_jump(jump_next, len(self.chunk.instructions))

        # 5. Else block
        if node.else_block:
            for stmt in node.else_block.body:
                self._compile_statement(stmt)

        # 6. Patch all jumps to end
        end_ip = len(self.chunk.instructions)
        for j in jumps_to_end:
            self.chunk.patch_jump(j, end_ip)

    def _compile_while(self, node: WhileStmt) -> None:
        loop_start = len(self.chunk.instructions)
        self._continue_stack.append(loop_start)
        self._break_stack.append([])

        self._compile_expression(node.condition)
        jump_out = self.chunk.emit(OpCode.POP_JUMP_IF_FALSE, 0, line=node.line, col=node.col)

        for stmt in node.body.body:
            self._compile_statement(stmt)

        self.chunk.emit(OpCode.JUMP_ABSOLUTE, loop_start)
        loop_end = len(self.chunk.instructions)
        self.chunk.patch_jump(jump_out, loop_end)

        # Patch breaks
        for b in self._break_stack.pop():
            self.chunk.patch_jump(b, loop_end)
        self._continue_stack.pop()

    def _compile_loop(self, node: LoopStmt) -> None:
        loop_start = len(self.chunk.instructions)
        self._continue_stack.append(loop_start)
        self._break_stack.append([])

        for stmt in node.body.body:
            self._compile_statement(stmt)

        self.chunk.emit(OpCode.JUMP_ABSOLUTE, loop_start, line=node.line, col=node.col)
        loop_end = len(self.chunk.instructions)

        for b in self._break_stack.pop():
            self.chunk.patch_jump(b, loop_end)
        self._continue_stack.pop()

    def _compile_for_each(self, node: ForEachStmt) -> None:
        # Push iterable and get iterator
        self._compile_expression(node.iterable)
        self.chunk.emit(OpCode.GET_ITER, line=node.line, col=node.col)

        loop_start = len(self.chunk.instructions)
        self._continue_stack.append(loop_start)
        self._break_stack.append([])

        for_iter_idx = self.chunk.emit(OpCode.FOR_ITER, 0, line=node.line, col=node.col)
        # Store loop variable
        var_idx = self.chunk.add_name(node.var)
        self.chunk.emit(OpCode.STORE_NAME, var_idx, node.var)

        # Loop body
        for stmt in node.body.body:
            self._compile_statement(stmt)

        self.chunk.emit(OpCode.JUMP_ABSOLUTE, loop_start)
        loop_end = len(self.chunk.instructions)
        self.chunk.patch_jump(for_iter_idx, loop_end)

        for b in self._break_stack.pop():
            self.chunk.patch_jump(b, loop_end)
        self._continue_stack.pop()

    def _compile_match(self, node: MatchStmt) -> None:
        # Subject expression
        self._compile_expression(node.subject)
        end_jumps: list[int] = []

        for arm in node.arms:
            self.chunk.emit(OpCode.DUP_TOP) # duplicate subject for comparison
            self._compile_expression(arm.pattern)
            cmp_idx = CMP_SYMBOLS.index("==")
            self.chunk.emit(OpCode.COMPARE_OP, cmp_idx, "==")
            jump_next = self.chunk.emit(OpCode.POP_JUMP_IF_FALSE, 0)

            # Match arm body
            self.chunk.emit(OpCode.POP_TOP) # pop duplicated subject
            if isinstance(arm.body, Block):
                for s in arm.body.body:
                    self._compile_statement(s)
            else:
                self._compile_expression(arm.body)
                self.chunk.emit(OpCode.POP_TOP)

            end_jumps.append(self.chunk.emit(OpCode.JUMP_ABSOLUTE, 0))
            self.chunk.patch_jump(jump_next, len(self.chunk.instructions))

        # Default arm
        self.chunk.emit(OpCode.POP_TOP) # pop subject
        if node.default:
            if isinstance(node.default, Block):
                for s in node.default.body:
                    self._compile_statement(s)
            else:
                self._compile_expression(node.default)
                self.chunk.emit(OpCode.POP_TOP)

        end_ip = len(self.chunk.instructions)
        for j in end_jumps:
            self.chunk.patch_jump(j, end_ip)

    # ── Expressions ───────────────────────────────────────────────────────────

    def _compile_expression(self, node: Node) -> None:
        match node.__class__.__name__:
            case "IntLiteral" | "FloatLiteral" | "StringLiteral":
                idx = self.chunk.add_constant(node.value) # type: ignore
                self.chunk.emit(OpCode.LOAD_CONST, idx, node.value, line=node.line, col=node.col) # type: ignore

            case "BoolLiteral":
                idx = self.chunk.add_constant(node.value) # type: ignore
                self.chunk.emit(OpCode.LOAD_CONST, idx, node.value, line=node.line, col=node.col) # type: ignore

            case "NullLiteral":
                idx = self.chunk.add_constant(None)
                self.chunk.emit(OpCode.LOAD_CONST, idx, None, line=node.line, col=node.col)

            case "Identifier":
                name_idx = self.chunk.add_name(node.name) # type: ignore
                self.chunk.emit(OpCode.LOAD_NAME, name_idx, node.name, line=node.line, col=node.col) # type: ignore

            case "FStringLiteral":
                for part in node.parts: # type: ignore
                    if isinstance(part, str):
                        c_idx = self.chunk.add_constant(part)
                        self.chunk.emit(OpCode.LOAD_CONST, c_idx, part, line=node.line, col=node.col)
                    else:
                        self._compile_expression(part)
                        self.chunk.emit(OpCode.FORMAT_VALUE, line=node.line, col=node.col)
                self.chunk.emit(OpCode.BUILD_STRING, len(node.parts), line=node.line, col=node.col) # type: ignore

            case "BinaryOp":
                self._compile_binary_op(node) # type: ignore

            case "UnaryOp":
                self._compile_unary_op(node) # type: ignore

            case "Assignment":
                self._compile_expression(node.value) # type: ignore
                name_idx = self.chunk.add_name(node.name) # type: ignore
                self.chunk.emit(OpCode.STORE_NAME, name_idx, node.name, line=node.line, col=node.col) # type: ignore
                # Load back for expression value
                self.chunk.emit(OpCode.LOAD_NAME, name_idx, node.name, line=node.line, col=node.col) # type: ignore

            case "IndexAssignment":
                self._compile_expression(node.obj) # type: ignore
                self._compile_expression(node.index) # type: ignore
                self._compile_expression(node.value) # type: ignore
                self.chunk.emit(OpCode.STORE_SUBSCR, line=node.line, col=node.col)
                # Reload value for expression chaining
                self._compile_expression(node.value) # type: ignore

            case "Call":
                self._compile_call(node) # type: ignore

            case "MethodCall":
                self._compile_method_call(node) # type: ignore

            case "Index":
                self._compile_expression(node.obj) # type: ignore
                self._compile_expression(node.index) # type: ignore
                self.chunk.emit(OpCode.BINARY_SUBSCR, line=node.line, col=node.col)

            case "ArrayLiteral":
                for el in node.elements: # type: ignore
                    self._compile_expression(el)
                self.chunk.emit(OpCode.BUILD_LIST, len(node.elements), line=node.line, col=node.col) # type: ignore

            case "MapLiteral":
                for k, v in node.pairs: # type: ignore
                    self._compile_expression(k)
                    self._compile_expression(v)
                self.chunk.emit(OpCode.BUILD_MAP, len(node.pairs), line=node.line, col=node.col) # type: ignore

            case "TupleLiteral":
                for el in node.elements: # type: ignore
                    self._compile_expression(el)
                self.chunk.emit(OpCode.BUILD_TUPLE, len(node.elements), line=node.line, col=node.col) # type: ignore

            case "Closure":
                self._compile_closure(node) # type: ignore

            case _:
                raise NotImplementedError(f"Cannot compile expression node: {node.__class__.__name__}")

    def _compile_binary_op(self, node: BinaryOp) -> None:
        op = node.operator

        # Short-circuit logical AND
        if op == "&&":
            self._compile_expression(node.left)
            jump_false = self.chunk.emit(OpCode.JUMP_IF_FALSE_OR_POP, 0, line=node.line, col=node.col)
            self._compile_expression(node.right)
            self.chunk.patch_jump(jump_false, len(self.chunk.instructions))
            return

        # Short-circuit logical OR
        if op == "||":
            self._compile_expression(node.left)
            jump_true = self.chunk.emit(OpCode.JUMP_IF_TRUE_OR_POP, 0, line=node.line, col=node.col)
            self._compile_expression(node.right)
            self.chunk.patch_jump(jump_true, len(self.chunk.instructions))
            return

        # Comparisons
        if op in CMP_SYMBOLS:
            self._compile_expression(node.left)
            self._compile_expression(node.right)
            cmp_idx = CMP_SYMBOLS.index(op)
            self.chunk.emit(OpCode.COMPARE_OP, cmp_idx, op, line=node.line, col=node.col)
            return

        # Range expression 1..10 -> calls range(start, end)
        if op == "..":
            name_idx = self.chunk.add_name("range")
            self.chunk.emit(OpCode.LOAD_NAME, name_idx, "range", line=node.line, col=node.col)
            self._compile_expression(node.left)
            self._compile_expression(node.right)
            self.chunk.emit(OpCode.CALL_FUNCTION, 2, line=node.line, col=node.col)
            return

        # Standard arithmetic
        self._compile_expression(node.left)
        self._compile_expression(node.right)

        match op:
            case "+":  self.chunk.emit(OpCode.BINARY_ADD, line=node.line, col=node.col)
            case "-":  self.chunk.emit(OpCode.BINARY_SUB, line=node.line, col=node.col)
            case "*":  self.chunk.emit(OpCode.BINARY_MUL, line=node.line, col=node.col)
            case "/":  self.chunk.emit(OpCode.BINARY_DIV, line=node.line, col=node.col)
            case "%":  self.chunk.emit(OpCode.BINARY_MOD, line=node.line, col=node.col)
            case "**": self.chunk.emit(OpCode.BINARY_POW, line=node.line, col=node.col)
            case _:    raise NotImplementedError(f"Unsupported binary operator: '{op}'")

    def _compile_unary_op(self, node: UnaryOp) -> None:
        self._compile_expression(node.operand)
        match node.operator:
            case "-": self.chunk.emit(OpCode.UNARY_NEGATIVE, line=node.line, col=node.col)
            case "!": self.chunk.emit(OpCode.UNARY_NOT, line=node.line, col=node.col)
            case _:   raise NotImplementedError(f"Unsupported unary operator: '{node.operator}'")

    def _compile_call(self, node: Call) -> None:
        # Special optimization for cheppu(...) -> PRINT_EXPR
        if isinstance(node.callee, Identifier) and node.callee.name == "cheppu":
            for arg in node.arguments:
                self._compile_expression(arg)
            self.chunk.emit(OpCode.PRINT_EXPR, len(node.arguments), line=node.line, col=node.col)
            return

        self._compile_expression(node.callee)
        for arg in node.arguments:
            self._compile_expression(arg)
        self.chunk.emit(OpCode.CALL_FUNCTION, len(node.arguments), line=node.line, col=node.col)

    def _compile_method_call(self, node: MethodCall) -> None:
        # obj.method(args) -> load __call_method__, push obj, push method_name, push args
        call_method_idx = self.chunk.add_name("__call_method__")
        self.chunk.emit(OpCode.LOAD_NAME, call_method_idx, "__call_method__", line=node.line, col=node.col)
        self._compile_expression(node.obj)
        method_name_idx = self.chunk.add_constant(node.method)
        self.chunk.emit(OpCode.LOAD_CONST, method_name_idx, node.method, line=node.line, col=node.col)
        for arg in node.args:
            self._compile_expression(arg)
        self.chunk.emit(OpCode.CALL_FUNCTION, 2 + len(node.args), line=node.line, col=node.col)


    def _compile_closure(self, node: Closure) -> None:
        func_compiler = BytecodeCompiler(filename=self.filename)
        func_chunk = CodeChunk(name="<muppu>", filename=self.filename)
        func_chunk.argnames = [p.name for p in node.params]
        func_compiler.chunk = func_chunk

        if isinstance(node.body, Block):
            for stmt in node.body.body:
                func_compiler._compile_statement(stmt)
        else:
            func_compiler._compile_expression(node.body)
            func_compiler.chunk.emit(OpCode.RETURN_VALUE)

        none_idx = func_chunk.add_constant(None)
        func_chunk.emit(OpCode.LOAD_CONST, none_idx, None)
        func_chunk.emit(OpCode.RETURN_VALUE)

        chunk_idx = self.chunk.add_constant(func_chunk)
        self.chunk.emit(OpCode.LOAD_CONST, chunk_idx, func_chunk, line=node.line, col=node.col)
        self.chunk.emit(OpCode.MAKE_FUNCTION, line=node.line, col=node.col)
