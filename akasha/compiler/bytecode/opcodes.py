"""
Akasha Bytecode — Instruction Set and OpCodes
==============================================

Defines all stack-based VM instructions used by the Akasha compiler and VM.
"""

from __future__ import annotations
from enum import IntEnum, auto
from dataclasses import dataclass
from typing import Any, Optional


class OpCode(IntEnum):
    # ── Stack Manipulation ───────────────────────────────────────────────────
    NOP = auto()
    POP_TOP = auto()
    DUP_TOP = auto()
    ROT_TWO = auto()

    # ── Constants & Names ────────────────────────────────────────────────────
    LOAD_CONST = auto()        # arg: index into constants pool
    LOAD_NAME = auto()         # arg: index into names table (looks in locals, then globals, then builtins)
    STORE_NAME = auto()        # arg: index into names table
    LOAD_GLOBAL = auto()       # arg: index into names table
    STORE_GLOBAL = auto()      # arg: index into names table
    LOAD_FAST = auto()         # arg: local variable slot index
    STORE_FAST = auto()        # arg: local variable slot index

    # ── Arithmetic & Unary Operators ─────────────────────────────────────────
    BINARY_ADD = auto()        # pop b, pop a -> push a + b
    BINARY_SUB = auto()        # pop b, pop a -> push a - b
    BINARY_MUL = auto()        # pop b, pop a -> push a * b
    BINARY_DIV = auto()        # pop b, pop a -> push a / b
    BINARY_MOD = auto()        # pop b, pop a -> push a % b
    BINARY_POW = auto()        # pop b, pop a -> push a ** b
    UNARY_NEGATIVE = auto()    # pop a -> push -a
    UNARY_NOT = auto()         # pop a -> push not a

    # ── Comparison Operators ─────────────────────────────────────────────────
    COMPARE_OP = auto()        # arg: comparison type (0: '==', 1: '!=', 2: '<', 3: '<=', 4: '>', 5: '>=')

    # ── Control Flow & Jumps ─────────────────────────────────────────────────
    JUMP_ABSOLUTE = auto()     # arg: target instruction index
    JUMP_FORWARD = auto()      # arg: relative offset
    POP_JUMP_IF_FALSE = auto() # pop a, if not a: jump to arg
    POP_JUMP_IF_TRUE = auto()  # pop a, if a: jump to arg
    JUMP_IF_FALSE_OR_POP = auto() # if stack top is false: jump to arg; else pop
    JUMP_IF_TRUE_OR_POP = auto()  # if stack top is true: jump to arg; else pop

    # ── Collections ──────────────────────────────────────────────────────────
    BUILD_LIST = auto()        # arg: number of elements on stack
    BUILD_MAP = auto()         # arg: number of key-value pairs (2 * arg elements on stack)
    BUILD_TUPLE = auto()       # arg: number of elements on stack
    BINARY_SUBSCR = auto()     # pop index, pop container -> push container[index]
    STORE_SUBSCR = auto()      # pop value, pop index, pop container -> container[index] = value

    # ── Iteration ────────────────────────────────────────────────────────────
    GET_ITER = auto()          # pop iterable -> push iterator
    FOR_ITER = auto()          # call next(iter). If exhausted: jump to arg; else: push next item

    # ── Functions & Calls ────────────────────────────────────────────────────
    MAKE_FUNCTION = auto()     # pop code_obj -> push AkashaFunction
    CALL_FUNCTION = auto()     # arg: number of positional arguments -> call callable
    RETURN_VALUE = auto()      # pop return_val -> return from current frame

    # ── Built-in I/O ─────────────────────────────────────────────────────────
    PRINT_EXPR = auto()        # arg: number of args -> print them (like cheppu)
    FORMAT_VALUE = auto()      # pop val -> push str(val)
    BUILD_STRING = auto()      # arg: number of string parts -> concatenate into single string


CMP_SYMBOLS = ["==", "!=", "<", "<=", ">", ">="]


@dataclass
class Instruction:
    """A single bytecode instruction."""
    opcode: OpCode
    arg: int = 0
    argval: Any = None
    line: int = 0
    col: int = 0

    def __repr__(self) -> str:
        name = self.opcode.name
        arg_str = f" {self.arg}" if self.arg != 0 or self.opcode in (OpCode.LOAD_CONST, OpCode.LOAD_NAME, OpCode.STORE_NAME, OpCode.COMPARE_OP, OpCode.CALL_FUNCTION) else ""
        val_str = f" ({self.argval!r})" if self.argval is not None else ""
        return f"{name:<20}{arg_str}{val_str}"
