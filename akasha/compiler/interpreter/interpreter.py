"""
Akasha Programming Language — Tree-Walking Interpreter
====================================================

Evaluates a Akasha AST by walking the tree recursively.

This is the v0.1 runtime — an interpreter, not a compiler.
A native LLVM-backed compiler will replace this in v0.7.

Design:
- Pure tree-walker: visit each AST node, return a Akasha runtime value
- Lexical scoping via Environment chain
- Built-in functions registered at startup
- Control flow via Python exceptions (ReturnSignal, BreakSignal, etc.)
- Clear runtime errors with source location when available
"""

from __future__ import annotations
import math
import os
import sys
import time
from typing import Any, Optional

from ..ast_nodes.nodes import (
    Program, Block, Node,
    IntLiteral, FloatLiteral, StringLiteral, FStringLiteral,
    BoolLiteral, NullLiteral,
    Identifier, BinaryOp, UnaryOp, Assignment, Call, Index, Slice, IndexAssignment,
    FieldAccess, ArrayLiteral, MapLiteral, TupleLiteral, RangeExpr,
    Closure, MethodCall, StructLiteral, PropagateError,
    ExprStatement, VarDecl, ConstDecl, SecretDecl,
    FunctionDecl, ReturnStmt, IfStmt, WhileStmt, ForEachStmt,
    LoopStmt, BreakStmt, ContinueStmt, MatchStmt, MatchArm,
    ImportStmt, ExportStmt, StructDecl, EnumDecl,
    TraitDecl, ImplBlock, UnsafeBlock,
)
from .values import (
    SHUNYAM, AkashaNullType,
    AkashaInt, AkashaFloat, AkashaBool, AkashaString,
    AkashaArray, AkashaMap, AkashaTuple,
    AkashaOption, AkashaResult,
    AkashaFunction, AkashaClosure, AkashaBuiltin, AkashaStruct,
    Environment,
    ReturnSignal, BreakSignal, ContinueSignal,
    AkashaRuntimeError,
)


# ── Type coercion helpers ─────────────────────────────────────────────────────

def _to_python_bool(val: Any) -> bool:
    """Convert a Akasha value to a Python bool for condition checks."""
    if isinstance(val, AkashaBool):
        return val.value
    if isinstance(val, AkashaNullType):
        return False
    if isinstance(val, AkashaInt):
        return val.value != 0
    if isinstance(val, AkashaFloat):
        return val.value != 0.0
    if isinstance(val, AkashaString):
        return len(val.value) > 0
    if isinstance(val, AkashaArray):
        return len(val.elements) > 0
    return True


def _to_display_str(val: Any) -> str:
    """Convert a Akasha value to its display string for cheppu()."""
    if isinstance(val, AkashaString):
        return val.value
    if isinstance(val, AkashaBool):
        return "nijam" if val.value else "abaddham"
    if isinstance(val, AkashaNullType):
        return "shunyam"
    if isinstance(val, AkashaInt):
        return str(val.value)
    if isinstance(val, AkashaFloat):
        # Show clean float
        f = val.value
        if f == int(f):
            return f"{f:.1f}"
        return str(f)
    if isinstance(val, AkashaArray):
        items = ", ".join(_to_display_str(e) for e in val.elements)
        return f"[{items}]"
    if isinstance(val, AkashaMap):
        items = ", ".join(f"{_to_display_str(k)}: {_to_display_str(v)}"
                          for k, v in val.pairs.items())
        return "{" + items + "}"
    if isinstance(val, AkashaTuple):
        items = ", ".join(_to_display_str(e) for e in val.elements)
        return f"({items})"
    if isinstance(val, AkashaStruct):
        items = ", ".join(f"{k}: {_to_display_str(v)}" for k, v in val.fields.items())
        return f"{val.type_name} {{ {items} }}"
    if isinstance(val, AkashaOption):
        if val.has_value:
            return f"Undu({_to_display_str(val.value)})"
        return "Ledu"
    if isinstance(val, AkashaResult):
        if val.ok:
            return f"Sari({_to_display_str(val.value)})"
        return f"Tappu({_to_display_str(val.error)})"
    if callable(val):
        return repr(val)
    return str(val)


def _akasha_eq(a: Any, b: Any) -> bool:
    """Structural equality between two Akasha values."""
    if type(a) != type(b):
        # Special numeric comparison
        if isinstance(a, (AkashaInt, AkashaFloat)) and isinstance(b, (AkashaInt, AkashaFloat)):
            return _numeric(a) == _numeric(b)
        return False
    if isinstance(a, AkashaNullType):
        return True  # shunyam == shunyam
    return a == b


def _numeric(v: Any) -> float:
    if isinstance(v, AkashaInt):
        return float(v.value)
    if isinstance(v, AkashaFloat):
        return v.value
    raise AkashaRuntimeError(f"Expected a number, got {type(v).__name__}")


# ── Built-in Functions ────────────────────────────────────────────────────────

def _builtin_cheppu(args: list[Any]) -> Any:
    """cheppu(...) — print to stdout"""
    parts = [_to_display_str(a) for a in args]
    print(" ".join(parts))
    return SHUNYAM


def _builtin_adugu(args: list[Any]) -> Any:
    """adugu(prompt) — read line from stdin"""
    prompt = _to_display_str(args[0]) if args else ""
    try:
        line = input(prompt)
        return AkashaString(line)
    except EOFError:
        return AkashaString("")


def _builtin_pari(args: list[Any]) -> Any:
    """pari(condition, message?) — assert"""
    if not args:
        raise AkashaRuntimeError("pari() requires at least one argument")
    cond = args[0]
    msg  = _to_display_str(args[1]) if len(args) > 1 else "Assertion failed"
    if not _to_python_bool(cond):
        raise AkashaRuntimeError(f"Assertion failed: {msg}")
    return SHUNYAM


def _builtin_parimaanam(args: list[Any]) -> Any:
    """parimaanam(collection) — length"""
    if not args:
        raise AkashaRuntimeError("parimaanam() requires one argument")
    v = args[0]
    if isinstance(v, AkashaString):
        return AkashaInt(len(v.value))
    if isinstance(v, (AkashaArray, AkashaTuple)):
        return AkashaInt(len(v.elements))
    if isinstance(v, AkashaMap):
        return AkashaInt(len(v.pairs))
    raise AkashaRuntimeError(f"parimaanam() does not support {type(v).__name__}")


def _builtin_type_of(args: list[Any]) -> Any:
    """type_of(value) — return the Akasha type name as a string"""
    if not args:
        raise AkashaRuntimeError("type_of() requires one argument")
    v = args[0]
    mapping = {
        AkashaInt:      "Sankhya",
        AkashaFloat:    "Dasamsam",
        AkashaBool:     "Nijam",
        AkashaString:   "Padam",
        AkashaNullType: "Shunyam",
        AkashaArray:    "Patrika",
        AkashaMap:      "Naksha",
        AkashaTuple:    "Janta",
        AkashaOption:   "Vikalpa",
        AkashaResult:   "Phalitham",
        AkashaFunction: "Karyam",
        AkashaClosure:  "Muppu",
        AkashaBuiltin:  "Builtin",
    }
    for t, name in mapping.items():
        if isinstance(v, t):
            return AkashaString(name)
    if isinstance(v, AkashaStruct):
        return AkashaString(v.type_name)
    return AkashaString("Unknown")


def _builtin_sankhya(args: list[Any]) -> Any:
    """Sankhya(x) — convert to integer"""
    if not args:
        raise AkashaRuntimeError("Sankhya() requires one argument")
    v = args[0]
    if isinstance(v, AkashaInt):
        return v
    if isinstance(v, AkashaFloat):
        return AkashaInt(int(v.value))
    if isinstance(v, AkashaString):
        try:
            return AkashaInt(int(v.value))
        except ValueError:
            raise AkashaRuntimeError(f"Cannot convert '{v.value}' to Sankhya")
    if isinstance(v, AkashaBool):
        return AkashaInt(1 if v.value else 0)
    raise AkashaRuntimeError(f"Cannot convert {type(v).__name__} to Sankhya")


def _builtin_dasamsam(args: list[Any]) -> Any:
    """Dasamsam(x) — convert to float"""
    if not args:
        raise AkashaRuntimeError("Dasamsam() requires one argument")
    v = args[0]
    if isinstance(v, AkashaFloat):
        return v
    if isinstance(v, AkashaInt):
        return AkashaFloat(float(v.value))
    if isinstance(v, AkashaString):
        try:
            return AkashaFloat(float(v.value))
        except ValueError:
            raise AkashaRuntimeError(f"Cannot convert '{v.value}' to Dasamsam")
    raise AkashaRuntimeError(f"Cannot convert {type(v).__name__} to Dasamsam")


def _builtin_padam(args: list[Any]) -> Any:
    """Padam(x) — convert to string"""
    if not args:
        raise AkashaRuntimeError("Padam() requires one argument")
    return AkashaString(_to_display_str(args[0]))


def _builtin_environment(args: list[Any]) -> Any:
    """environment(key) — read environment variable"""
    if not args:
        raise AkashaRuntimeError("environment() requires one argument")
    key = args[0]
    if not isinstance(key, AkashaString):
        raise AkashaRuntimeError("environment() expects a Padam (string) argument")
    val = os.environ.get(key.value)
    if val is None:
        return SHUNYAM
    return AkashaString(val)


def _builtin_range(args: list[Any]) -> Any:
    """range(start, end) or range(end) — create an array of integers"""
    if len(args) == 1:
        end   = int(_numeric(args[0]))
        start = 0
    elif len(args) == 2:
        start = int(_numeric(args[0]))
        end   = int(_numeric(args[1]))
    else:
        raise AkashaRuntimeError("range() takes 1 or 2 arguments")
    return AkashaArray([AkashaInt(i) for i in range(start, end)])


BUILTINS: dict[str, Any] = {
    "cheppu":       AkashaBuiltin("cheppu",       _builtin_cheppu),
    "adugu":        AkashaBuiltin("adugu",         _builtin_adugu),
    "pari":         AkashaBuiltin("pari",          _builtin_pari),
    "parimaanam":   AkashaBuiltin("parimaanam",    _builtin_parimaanam),
    "type_of":      AkashaBuiltin("type_of",       _builtin_type_of),
    "Sankhya":      AkashaBuiltin("Sankhya",       _builtin_sankhya),
    "Dasamsam":     AkashaBuiltin("Dasamsam",      _builtin_dasamsam),
    "Padam":        AkashaBuiltin("Padam",         _builtin_padam),
    "environment":  AkashaBuiltin("environment",   _builtin_environment),
    "range":        AkashaBuiltin("range",         _builtin_range),
    # Math constants
    "PI":           AkashaFloat(math.pi),
    "E":            AkashaFloat(math.e),
}


# ── Interpreter ───────────────────────────────────────────────────────────────

class Interpreter:
    """
    Tree-walking interpreter for Akasha v0.1.

    Usage:
        interp = Interpreter()
        interp.execute(program_ast)
    """

    def __init__(self) -> None:
        self._globals = Environment()
        self._struct_defs: dict[str, list[tuple[str, Any]]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        for name, val in BUILTINS.items():
            self._globals.define(name, val)

    # ── Public entry points ───────────────────────────────────────────────────

    def execute(self, program: Program) -> None:
        """Execute a full program in the global scope."""
        self._exec_block_body(program.body, self._globals)

    def execute_expression(self, node: Node, env: Optional[Environment] = None) -> Any:
        """Evaluate a single expression (used by REPL)."""
        return self._eval(node, env or self._globals)

    # ── Statement executor ────────────────────────────────────────────────────

    def _exec(self, node: Node, env: Environment) -> Any:
        """Dispatch a statement node."""
        match type(node).__name__:
            case "VarDecl":        return self._exec_var_decl(node, env)
            case "ConstDecl":      return self._exec_const_decl(node, env)
            case "SecretDecl":     return self._exec_secret_decl(node, env)
            case "FunctionDecl":   return self._exec_function_decl(node, env)
            case "ReturnStmt":     return self._exec_return(node, env)
            case "IfStmt":         return self._exec_if(node, env)
            case "WhileStmt":      return self._exec_while(node, env)
            case "ForEachStmt":    return self._exec_for_each(node, env)
            case "LoopStmt":       return self._exec_loop(node, env)
            case "BreakStmt":      raise BreakSignal()
            case "ContinueStmt":   raise ContinueSignal()
            case "MatchStmt":      return self._exec_match(node, env)
            case "ImportStmt":     return self._exec_import(node, env)
            case "ExportStmt":     return self._exec(node.decl, env)
            case "StructDecl":     return self._exec_struct_decl(node, env)
            case "EnumDecl":       return self._exec_enum_decl(node, env)
            case "TraitDecl":      return SHUNYAM  # v0.1: traits stored, not enforced
            case "ImplBlock":      return self._exec_impl_block(node, env)
            case "UnsafeBlock":    return self._exec_block_body(node.body.body, env)
            case "ExprStatement":  return self._eval(node.expr, env)
            case "Block":          return self._exec_block_body(node.body, env.child())
            case _:
                return self._eval(node, env)

    def _exec_block_body(self, stmts: list[Node], env: Environment) -> Any:
        result: Any = SHUNYAM
        for stmt in stmts:
            result = self._exec(stmt, env)
        return result

    # ── Variable declarations ──────────────────────────────────────────────────

    def _exec_var_decl(self, node: VarDecl, env: Environment) -> Any:
        val = self._eval(node.value, env)
        env.define(node.name, val)
        return SHUNYAM

    def _exec_const_decl(self, node: ConstDecl, env: Environment) -> Any:
        val = self._eval(node.value, env)
        env.define(node.name, val)
        return SHUNYAM

    def _exec_secret_decl(self, node: SecretDecl, env: Environment) -> Any:
        val = self._eval(node.value, env)
        # Wrap secret in a special marker so it never leaks through cheppu
        env.define(node.name, _SecretValue(val))
        return SHUNYAM

    # ── Functions ──────────────────────────────────────────────────────────────

    def _exec_function_decl(self, node: FunctionDecl, env: Environment) -> Any:
        fn = AkashaFunction(
            name=node.name,
            params=node.params,
            body=node.body,
            closure=env,
            is_async=node.is_async,
        )
        env.define(node.name, fn)
        return SHUNYAM

    def _exec_return(self, node: ReturnStmt, env: Environment) -> Any:
        val = self._eval(node.value, env) if node.value else SHUNYAM
        raise ReturnSignal(val)

    def _call_function(self, fn: Any, args: list[Any], call_node: Optional[Node] = None) -> Any:
        """Invoke a callable Akasha value."""
        if isinstance(fn, AkashaBuiltin):
            return fn.fn(args)

        if isinstance(fn, (AkashaFunction, AkashaClosure)):
            params = fn.params
            fn_env = fn.closure.child()

            # Bind positional arguments, fill defaults
            for i, param in enumerate(params):
                if i < len(args):
                    fn_env.define(param.name, args[i])
                elif param.default is not None:
                    fn_env.define(param.name, self._eval(param.default, fn.closure))
                else:
                    raise AkashaRuntimeError(
                        f"Missing argument '{param.name}' in call"
                    )

            # Extra args
            if len(args) > len(params):
                raise AkashaRuntimeError(
                    f"Too many arguments: expected {len(params)}, got {len(args)}"
                )

            try:
                if isinstance(fn, AkashaFunction):
                    return self._exec_block_body(fn.body.body, fn_env)
                else:
                    # Closure body can be a Block or a single expression
                    from ..ast_nodes.nodes import Block as BlockNode
                    if isinstance(fn.body, BlockNode):
                        return self._exec_block_body(fn.body.body, fn_env)
                    else:
                        return self._eval(fn.body, fn_env)
            except ReturnSignal as r:
                return r.value

        raise AkashaRuntimeError(
            f"{repr(fn)} is not callable.\n"
            f"  Only functions (karyam) and closures (muppu) can be called."
        )

    # ── Control flow ───────────────────────────────────────────────────────────

    def _exec_if(self, node: IfStmt, env: Environment) -> Any:
        if _to_python_bool(self._eval(node.condition, env)):
            return self._exec_block_body(node.then_block.body, env.child())
        for elif_cond, elif_block in node.elif_arms:
            if _to_python_bool(self._eval(elif_cond, env)):
                return self._exec_block_body(elif_block.body, env.child())
        if node.else_block:
            return self._exec_block_body(node.else_block.body, env.child())
        return SHUNYAM

    def _exec_while(self, node: WhileStmt, env: Environment) -> Any:
        while _to_python_bool(self._eval(node.condition, env)):
            try:
                self._exec_block_body(node.body.body, env.child())
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        return SHUNYAM

    def _exec_for_each(self, node: ForEachStmt, env: Environment) -> Any:
        iterable = self._eval(node.iterable, env)

        if isinstance(iterable, AkashaArray):
            items = iterable.elements
        elif isinstance(iterable, AkashaString):
            items = [AkashaString(c) for c in iterable.value]
        elif isinstance(iterable, RangeObj):
            items = [AkashaInt(i) for i in range(iterable.start, iterable.end)]
        else:
            raise AkashaRuntimeError(
                f"'prathi' loop requires an iterable (Patrika or range), "
                f"got {_to_display_str(iterable)}"
            )

        for item in items:
            loop_env = env.child()
            loop_env.define(node.var, item)
            try:
                self._exec_block_body(node.body.body, loop_env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        return SHUNYAM

    def _exec_loop(self, node: LoopStmt, env: Environment) -> Any:
        while True:
            try:
                self._exec_block_body(node.body.body, env.child())
            except BreakSignal:
                break
            except ContinueSignal:
                continue
        return SHUNYAM

    def _exec_match(self, node: MatchStmt, env: Environment) -> Any:
        subject = self._eval(node.subject, env)
        for arm in node.arms:
            pattern_val = self._eval(arm.pattern, env)
            if _akasha_eq(subject, pattern_val):
                arm_env = env.child()
                from ..ast_nodes.nodes import Block as BlockNode
                if isinstance(arm.body, BlockNode):
                    return self._exec_block_body(arm.body.body, arm_env)
                else:
                    return self._eval(arm.body, arm_env)
        if node.default is not None:
            from ..ast_nodes.nodes import Block as BlockNode
            if isinstance(node.default, BlockNode):
                return self._exec_block_body(node.default.body, env.child())
            else:
                return self._eval(node.default, env)
        return SHUNYAM

    # ── Struct / Enum ──────────────────────────────────────────────────────────

    def _exec_struct_decl(self, node: StructDecl, env: Environment) -> Any:
        self._struct_defs[node.name] = node.fields
        # Also register a constructor function
        def make_struct(args: list[Any]) -> Any:
            if len(args) != len(node.fields):
                raise AkashaRuntimeError(
                    f"Struct '{node.name}' expects {len(node.fields)} fields, got {len(args)}"
                )
            fields = {name: val for (name, _), val in zip(node.fields, args)}
            return AkashaStruct(type_name=node.name, fields=fields)
        env.define(node.name, AkashaBuiltin(node.name, make_struct))
        return SHUNYAM

    def _exec_enum_decl(self, node: EnumDecl, env: Environment) -> Any:
        # Register each variant as a callable or value
        for variant_name, type_params in node.variants:
            full_name = f"{node.name}.{variant_name}"
            if type_params:
                def make_variant(args: list[Any], vn=variant_name, tn=node.name) -> Any:
                    return AkashaStruct(
                        type_name=f"{tn}.{vn}",
                        fields={"value": args[0] if len(args) == 1 else AkashaArray(args)}
                    )
                env.define(full_name, AkashaBuiltin(full_name, make_variant))
            else:
                env.define(full_name, AkashaString(full_name))
        return SHUNYAM

    def _exec_impl_block(self, node: ImplBlock, env: Environment) -> Any:
        # Store methods associated with the type for method call dispatch
        for method in node.methods:
            method_key = f"{node.type_name}::{method.name}"
            fn = AkashaFunction(
                name=method_key,
                params=method.params,
                body=method.body,
                closure=env,
            )
            env.define(method_key, fn)
        return SHUNYAM

    # ── Imports ───────────────────────────────────────────────────────────────

    def _exec_import(self, node: ImportStmt, env: Environment) -> Any:
        module_name = node.module
        # v0.1: built-in standard library modules
        from ..stdlib import get_module
        module = get_module(module_name)
        if module is None:
            raise AkashaRuntimeError(
                f"Module '{module_name}' not found.",
                suggestion=f"Available modules: math, io, string"
            )
        if node.name:
            # digumathi func vethuku math
            val = module.get(node.name)
            if val is None:
                raise AkashaRuntimeError(
                    f"'{node.name}' not found in module '{module_name}'"
                )
            env.define(node.name, val)
        else:
            # digumathi math  → makes math.func available as math_func or via module object
            env.define(module_name, AkashaModule(module_name, module))
        return SHUNYAM

    # ══════════════════════════════════════════════════════════════════════════
    # EXPRESSION EVALUATOR
    # ══════════════════════════════════════════════════════════════════════════

    def _eval(self, node: Node, env: Environment) -> Any:
        """Evaluate an expression node and return its Akasha value."""
        match type(node).__name__:

            # ── Literals ──────────────────────────────────────────────────
            case "IntLiteral":
                return AkashaInt(node.value)
            case "FloatLiteral":
                return AkashaFloat(node.value)
            case "StringLiteral":
                return AkashaString(node.value)
            case "FStringLiteral":
                return self._eval_fstring(node, env)
            case "BoolLiteral":
                return AkashaBool(node.value)
            case "NullLiteral":
                return SHUNYAM
            case "ArrayLiteral":
                return AkashaArray([self._eval(e, env) for e in node.elements])
            case "MapLiteral":
                pairs: dict[Any, Any] = {}
                for k_node, v_node in node.pairs:
                    k = self._eval(k_node, env)
                    v = self._eval(v_node, env)
                    pairs[k] = v
                return AkashaMap(pairs)
            case "TupleLiteral":
                return AkashaTuple([self._eval(e, env) for e in node.elements])
            case "StructLiteral":
                return self._eval_struct_literal(node, env)

            # ── Identifiers ───────────────────────────────────────────────
            case "Identifier":
                try:
                    val = env.get(node.name)
                    if isinstance(val, _SecretValue):
                        raise AkashaRuntimeError(
                            f"Cannot use secret '{node.name}' directly.\n"
                            f"  Secrets are protected from accidental leakage."
                        )
                    return val
                except AkashaRuntimeError as e:
                    raise AkashaRuntimeError(str(e).strip(), node.line, node.col) from None

            # ── Index Assignment  arr[i] = val ───────────────────────────
            case "IndexAssignment":
                container = self._eval(node.obj, env)
                idx_val   = self._eval(node.index, env)
                new_val   = self._eval(node.value, env)
                if isinstance(container, AkashaArray):
                    if not isinstance(idx_val, AkashaInt):
                        raise AkashaRuntimeError("Array index must be Sankhya", node.line, node.col)
                    i = idx_val.value
                    if i < 0: i = len(container.elements) + i
                    if i < 0 or i >= len(container.elements):
                        raise AkashaRuntimeError(
                            f"Index {idx_val.value} out of bounds", node.line, node.col
                        )
                    container.elements[i] = new_val
                    return new_val
                if isinstance(container, AkashaMap):
                    container.pairs[idx_val] = new_val
                    return new_val
                raise AkashaRuntimeError(
                    f"Cannot index-assign into {_to_display_str(container)}", node.line, node.col
                )

            # ── Assignment ────────────────────────────────────────────────
            case "Assignment":
                val = self._eval(node.value, env)
                try:
                    env.assign(node.name, val)
                except AkashaRuntimeError:
                    env.define(node.name, val)
                return val

            # ── Binary Operations ─────────────────────────────────────────
            case "BinaryOp":
                return self._eval_binop(node, env)

            # ── Unary Operations ──────────────────────────────────────────
            case "UnaryOp":
                operand = self._eval(node.operand, env)
                if node.operator == "-":
                    if isinstance(operand, AkashaInt):
                        return AkashaInt(-operand.value)
                    if isinstance(operand, AkashaFloat):
                        return AkashaFloat(-operand.value)
                    raise AkashaRuntimeError(
                        f"Cannot negate {type(operand).__name__}",
                        node.line, node.col
                    )
                if node.operator == "!":
                    return AkashaBool(not _to_python_bool(operand))
                raise AkashaRuntimeError(f"Unknown unary operator: {node.operator}")

            # ── Calls ─────────────────────────────────────────────────────
            case "Call":
                callee = self._eval(node.callee, env)
                args   = [self._eval(a, env) for a in node.arguments]
                return self._call_function(callee, args, node)

            case "MethodCall":
                return self._eval_method_call(node, env)

            # ── Indexing & Slicing ────────────────────────────────────────
            case "Index":
                obj = self._eval(node.obj, env)
                idx = self._eval(node.index, env)
                return self._eval_index(obj, idx, node)

            case "Slice":
                obj   = self._eval(node.obj, env)
                start = self._eval(node.start, env)
                end   = self._eval(node.end, env)
                return self._eval_slice(obj, start, end, node)

            # ── Field Access ──────────────────────────────────────────────
            case "FieldAccess":
                obj = self._eval(node.obj, env)
                return self._eval_field(obj, node.field, node)

            # ── Range expression  0..10 ───────────────────────────────────
            case "RangeExpr":
                s = self._eval(node.start, env)
                e = self._eval(node.end, env)
                if not isinstance(s, AkashaInt) or not isinstance(e, AkashaInt):
                    raise AkashaRuntimeError("Range bounds must be Sankhya (integer)")
                return RangeObj(s.value, e.value)

            # ── Closure ───────────────────────────────────────────────────
            case "Closure":
                return AkashaClosure(params=node.params, body=node.body, closure=env)

            # ── Error propagation ─────────────────────────────────────────
            case "PropagateError":
                val = self._eval(node.expr, env)
                if isinstance(val, AkashaResult) and not val.ok:
                    raise ReturnSignal(val)
                if isinstance(val, AkashaResult):
                    return val.value
                return val

            # ── Passthrough for statement nodes (e.g., in block tails) ───
            case _:
                # Try executing as a statement
                return self._exec(node, env)

    # ── Binary operation dispatch ─────────────────────────────────────────────

    def _eval_binop(self, node: BinaryOp, env: Environment) -> Any:
        op    = node.operator
        left  = self._eval(node.left,  env)
        right = self._eval(node.right, env)

        # Range operator (..)
        if op == "..":
            if not isinstance(left, AkashaInt) or not isinstance(right, AkashaInt):
                raise AkashaRuntimeError("Range '..' requires integer bounds", node.line, node.col)
            return RangeObj(left.value, right.value)

        # Arithmetic
        if op in ("+", "-", "*", "/", "%", "**"):
            return self._eval_arithmetic(op, left, right, node)

        # Comparison
        if op in ("==", "!=", "<", "<=", ">", ">="):
            return self._eval_comparison(op, left, right, node)

        # Logical
        if op == "&&":
            return AkashaBool(_to_python_bool(left) and _to_python_bool(right))
        if op == "||":
            return AkashaBool(_to_python_bool(left) or _to_python_bool(right))

        raise AkashaRuntimeError(f"Unknown binary operator: {op}", node.line, node.col)

    def _eval_arithmetic(self, op: str, left: Any, right: Any, node: BinaryOp) -> Any:
        # String concatenation with +
        if op == "+" and isinstance(left, AkashaString) and isinstance(right, AkashaString):
            return AkashaString(left.value + right.value)

        # Array concatenation with +
        if op == "+" and isinstance(left, AkashaArray) and isinstance(right, AkashaArray):
            return AkashaArray(left.elements + right.elements)

        # Numeric operations
        if isinstance(left, (AkashaInt, AkashaFloat)) and isinstance(right, (AkashaInt, AkashaFloat)):
            lv = _numeric(left)
            rv = _numeric(right)
            if op == "+":  result = lv + rv
            elif op == "-": result = lv - rv
            elif op == "*": result = lv * rv
            elif op == "/":
                if rv == 0:
                    raise AkashaRuntimeError("Division by zero", node.line, node.col)
                result = lv / rv
            elif op == "%":
                if rv == 0:
                    raise AkashaRuntimeError("Modulo by zero", node.line, node.col)
                result = lv % rv
            elif op == "**":
                result = lv ** rv
            else:
                raise AkashaRuntimeError(f"Unknown arithmetic op: {op}")

            # Return int if both operands were int and result is whole
            if isinstance(left, AkashaInt) and isinstance(right, AkashaInt) and op != "/":
                if op != "**":
                    return AkashaInt(int(result))
                if result == int(result):
                    return AkashaInt(int(result))
            return AkashaFloat(float(result)) if isinstance(result, float) else AkashaInt(int(result))

        raise AkashaRuntimeError(
            f"Cannot apply '{op}' to {_to_display_str(left)} and {_to_display_str(right)}",
            node.line, node.col
        )

    def _eval_comparison(self, op: str, left: Any, right: Any, node: BinaryOp) -> Any:
        if op == "==":
            return AkashaBool(_akasha_eq(left, right))
        if op == "!=":
            return AkashaBool(not _akasha_eq(left, right))

        # Ordered comparisons require comparable types
        if isinstance(left, (AkashaInt, AkashaFloat)) and isinstance(right, (AkashaInt, AkashaFloat)):
            lv, rv = _numeric(left), _numeric(right)
            if op == "<":  return AkashaBool(lv < rv)
            if op == "<=": return AkashaBool(lv <= rv)
            if op == ">":  return AkashaBool(lv > rv)
            if op == ">=": return AkashaBool(lv >= rv)

        if isinstance(left, AkashaString) and isinstance(right, AkashaString):
            lv, rv = left.value, right.value
            if op == "<":  return AkashaBool(lv < rv)
            if op == "<=": return AkashaBool(lv <= rv)
            if op == ">":  return AkashaBool(lv > rv)
            if op == ">=": return AkashaBool(lv >= rv)

        raise AkashaRuntimeError(
            f"Cannot compare {_to_display_str(left)} and {_to_display_str(right)} with '{op}'",
            node.line, node.col
        )

    # ── Index / Slice ─────────────────────────────────────────────────────────

    def _eval_index(self, obj: Any, idx: Any, node: Node) -> Any:
        if isinstance(obj, AkashaArray):
            if not isinstance(idx, AkashaInt):
                raise AkashaRuntimeError("Array index must be Sankhya (integer)", node.line, node.col)
            i = idx.value
            if i < 0:
                i = len(obj.elements) + i
            if i < 0 or i >= len(obj.elements):
                raise AkashaRuntimeError(
                    f"Index {idx.value} out of bounds (length {len(obj.elements)})",
                    node.line, node.col
                )
            return obj.elements[i]
        if isinstance(obj, AkashaString):
            if not isinstance(idx, AkashaInt):
                raise AkashaRuntimeError("String index must be Sankhya (integer)", node.line, node.col)
            i = idx.value
            if i < 0:
                i = len(obj.value) + i
            if i < 0 or i >= len(obj.value):
                raise AkashaRuntimeError(
                    f"Index {idx.value} out of bounds (string length {len(obj.value)})",
                    node.line, node.col
                )
            return AkashaString(obj.value[i])
        if isinstance(obj, AkashaMap):
            val = obj.pairs.get(idx)
            if val is None:
                return SHUNYAM
            return val
        if isinstance(obj, AkashaTuple):
            if not isinstance(idx, AkashaInt):
                raise AkashaRuntimeError("Tuple index must be Sankhya", node.line, node.col)
            i = idx.value
            if i < 0 or i >= len(obj.elements):
                raise AkashaRuntimeError(f"Tuple index {i} out of bounds", node.line, node.col)
            return obj.elements[i]
        raise AkashaRuntimeError(
            f"{_to_display_str(obj)} does not support indexing",
            node.line, node.col
        )

    def _eval_slice(self, obj: Any, start: Any, end: Any, node: Node) -> Any:
        if isinstance(obj, AkashaArray):
            s = start.value if isinstance(start, AkashaInt) else int(_numeric(start))
            e = end.value   if isinstance(end,   AkashaInt) else int(_numeric(end))
            return AkashaArray(obj.elements[s:e])
        if isinstance(obj, AkashaString):
            s = start.value if isinstance(start, AkashaInt) else int(_numeric(start))
            e = end.value   if isinstance(end,   AkashaInt) else int(_numeric(end))
            return AkashaString(obj.value[s:e])
        raise AkashaRuntimeError(f"{_to_display_str(obj)} does not support slicing", node.line, node.col)

    # ── Field access ──────────────────────────────────────────────────────────

    def _eval_field(self, obj: Any, field: str, node: Node) -> Any:
        if isinstance(obj, AkashaStruct):
            if field in obj.fields:
                return obj.fields[field]
            raise AkashaRuntimeError(
                f"Struct '{obj.type_name}' has no field '{field}'",
                node.line, node.col
            )
        if isinstance(obj, AkashaResult):
            if field in ("ok", "tappudu"):
                return AkashaBool(obj.ok)
            if field == "value":
                return obj.value if obj.value is not None else SHUNYAM
            if field in ("error", "tappu"):
                return obj.error if obj.error is not None else SHUNYAM
        if isinstance(obj, AkashaOption):
            if field == "has_value":
                return AkashaBool(obj.has_value)
            if field == "value":
                return obj.value if obj.has_value else SHUNYAM
        if isinstance(obj, AkashaModule):
            val = obj.members.get(field)
            if val is None:
                raise AkashaRuntimeError(
                    f"Module '{obj.name}' has no member '{field}'",
                    node.line, node.col
                )
            return val
        raise AkashaRuntimeError(
            f"Cannot access field '{field}' on {_to_display_str(obj)}",
            node.line, node.col
        )

    # ── Method calls ──────────────────────────────────────────────────────────

    def _eval_method_call(self, node: MethodCall, env: Environment) -> Any:
        obj    = self._eval(node.obj, env)
        method = node.method
        args   = [self._eval(a, env) for a in node.args]

        # Array methods
        if isinstance(obj, AkashaArray):
            return self._array_method(obj, method, args, node)

        # String methods
        if isinstance(obj, AkashaString):
            return self._string_method(obj, method, args, node)

        # Map methods
        if isinstance(obj, AkashaMap):
            return self._map_method(obj, method, args, node)

        # Module method call  (module.func(args))
        if isinstance(obj, AkashaModule):
            fn = obj.members.get(method)
            if fn is None:
                raise AkashaRuntimeError(
                    f"Module '{obj.name}' has no function '{method}'",
                    node.line, node.col
                )
            return self._call_function(fn, args)

        # User-defined struct method (impl block)
        if isinstance(obj, AkashaStruct):
            method_key = f"{obj.type_name}::{method}"
            try:
                fn = env.get(method_key)
                args_with_self = [obj] + args
                return self._call_function(fn, args_with_self)
            except AkashaRuntimeError:
                pass

        raise AkashaRuntimeError(
            f"Type {_to_display_str(obj)} has no method '{method}'",
            node.line, node.col
        )

    def _array_method(self, arr: AkashaArray, method: str, args: list[Any], node: Node) -> Any:
        match method:
            case "cherchu" | "push":
                if not args:
                    raise AkashaRuntimeError("cherchu() requires one argument")
                arr.elements.append(args[0])
                return SHUNYAM
            case "rosi" | "pop":
                if not arr.elements:
                    raise AkashaRuntimeError("Cannot pop from empty array")
                return arr.elements.pop()
            case "parimaanam" | "length":
                return AkashaInt(len(arr.elements))
            case "map":
                if not args or not callable(args[0]) and not isinstance(args[0], (AkashaFunction, AkashaClosure, AkashaBuiltin)):
                    raise AkashaRuntimeError("map() requires a function argument")
                result = [self._call_function(args[0], [el]) for el in arr.elements]
                return AkashaArray(result)
            case "filter":
                if not args:
                    raise AkashaRuntimeError("filter() requires a function argument")
                result = [el for el in arr.elements
                          if _to_python_bool(self._call_function(args[0], [el]))]
                return AkashaArray(result)
            case "reduce":
                if len(args) < 1:
                    raise AkashaRuntimeError("reduce() requires a function argument")
                fn  = args[0]
                acc = args[1] if len(args) > 1 else arr.elements[0]
                start = 1 if len(args) == 1 else 0
                for el in arr.elements[start:]:
                    acc = self._call_function(fn, [acc, el])
                return acc
            case "reverse":
                return AkashaArray(list(reversed(arr.elements)))
            case "join":
                sep = args[0].value if args and isinstance(args[0], AkashaString) else ""
                return AkashaString(sep.join(_to_display_str(e) for e in arr.elements))
            case "contains" | "undu":
                if not args:
                    raise AkashaRuntimeError("contains() requires one argument")
                return AkashaBool(any(_akasha_eq(el, args[0]) for el in arr.elements))
            case "sort":
                def sort_key(v: Any) -> Any:
                    if isinstance(v, AkashaInt): return v.value
                    if isinstance(v, AkashaFloat): return v.value
                    if isinstance(v, AkashaString): return v.value
                    return 0
                return AkashaArray(sorted(arr.elements, key=sort_key))
            case _:
                raise AkashaRuntimeError(f"Patrika has no method '{method}'", node.line, node.col)

    def _string_method(self, s: AkashaString, method: str, args: list[Any], node: Node) -> Any:
        val = s.value
        match method:
            case "parimaanam" | "length":
                return AkashaInt(len(val))
            case "upper":
                return AkashaString(val.upper())
            case "lower":
                return AkashaString(val.lower())
            case "strip":
                return AkashaString(val.strip())
            case "split":
                sep = args[0].value if args and isinstance(args[0], AkashaString) else " "
                return AkashaArray([AkashaString(p) for p in val.split(sep)])
            case "starts_with":
                if not args: return AkashaBool(False)
                prefix = args[0].value if isinstance(args[0], AkashaString) else ""
                return AkashaBool(val.startswith(prefix))
            case "ends_with":
                if not args: return AkashaBool(False)
                suffix = args[0].value if isinstance(args[0], AkashaString) else ""
                return AkashaBool(val.endswith(suffix))
            case "contains":
                if not args: return AkashaBool(False)
                sub = args[0].value if isinstance(args[0], AkashaString) else ""
                return AkashaBool(sub in val)
            case "replace":
                if len(args) < 2: raise AkashaRuntimeError("replace() requires 2 arguments")
                old = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
                new = args[1].value if isinstance(args[1], AkashaString) else str(args[1])
                return AkashaString(val.replace(old, new))
            case _:
                raise AkashaRuntimeError(f"Padam has no method '{method}'", node.line, node.col)

    def _map_method(self, m: AkashaMap, method: str, args: list[Any], node: Node) -> Any:
        match method:
            case "keys":
                return AkashaArray(list(m.pairs.keys()))
            case "values":
                return AkashaArray(list(m.pairs.values()))
            case "contains" | "undu":
                if not args: return AkashaBool(False)
                return AkashaBool(args[0] in m.pairs)
            case "parimaanam" | "length":
                return AkashaInt(len(m.pairs))
            case _:
                raise AkashaRuntimeError(f"Naksha has no method '{method}'", node.line, node.col)

    # ── F-string evaluation ───────────────────────────────────────────────────

    def _eval_fstring(self, node: FStringLiteral, env: Environment) -> Any:
        parts: list[str] = []
        for part in node.parts:
            if isinstance(part, str):
                parts.append(part)
            else:
                val = self._eval(part, env)
                parts.append(_to_display_str(val))
        return AkashaString("".join(parts))

    # ── Struct literal ────────────────────────────────────────────────────────

    def _eval_struct_literal(self, node: StructLiteral, env: Environment) -> Any:
        fields: dict[str, Any] = {}
        for field_name, field_expr in node.fields:
            fields[field_name] = self._eval(field_expr, env)
        return AkashaStruct(type_name=node.name, fields=fields)


# ── Helper classes ────────────────────────────────────────────────────────────

class RangeObj:
    """Internal representation of a range (start..end)."""
    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end   = end

    def __repr__(self) -> str:
        return f"{self.start}..{self.end}"


class _SecretValue:
    """Wraps a secret value to prevent accidental leakage."""
    def __init__(self, val: Any) -> None:
        self._val = val

    def __repr__(self) -> str:
        return "<rahasyam: ***>"


class AkashaModule:
    """A loaded standard library module."""
    def __init__(self, name: str, members: dict[str, Any]) -> None:
        self.name    = name
        self.members = members

    def get(self, key: str) -> Optional[Any]:
        return self.members.get(key)

    def __repr__(self) -> str:
        return f"<modulu {self.name}>"
