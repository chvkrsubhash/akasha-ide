"""
Akasha Stack-Based Virtual Machine
===================================

Executes compiled Akasha bytecode chunks (.akb) at high speed.
"""

from __future__ import annotations
import sys
import io
from dataclasses import dataclass
from typing import Any, Optional, Callable
from ..compiler.bytecode.opcodes import OpCode, Instruction, CMP_SYMBOLS
from ..compiler.bytecode.serializer import CodeChunk
from ..compiler.interpreter.values import (
    AkashaInt, AkashaFloat, AkashaBool, AkashaString,
    AkashaArray, AkashaMap, AkashaTuple, SHUNYAM, _to_display_str
)


@dataclass
class VMFunction:
    """A user-defined function in the VM."""
    chunk: CodeChunk
    closure: dict[str, Any]

    def __repr__(self) -> str:
        return f"<karyam {self.chunk.name}>"


@dataclass
class CallFrame:
    """A single execution frame on the call stack."""
    chunk: CodeChunk
    ip: int = 0
    locals: dict[str, Any] = None # type: ignore

    def __post_init__(self) -> None:
        if self.locals is None:
            self.locals = {}


class AkashaVM:
    """Stack-based Virtual Machine executing Akasha bytecode."""

    def __init__(self, stdout: Optional[io.TextIOBase] = None) -> None:
        self.stdout = stdout or sys.stdout
        self.stack: list[Any] = []
        self.frames: list[CallFrame] = []
        self.globals: dict[str, Any] = {}
        self._init_builtins()

    def _init_builtins(self) -> None:
        """Register built-in functions."""
        self.globals["nijam"] = True
        self.globals["abaddham"] = False
        self.globals["shunyam"] = None

        self.globals["cheppu"] = self._builtin_cheppu
        self.globals["range"] = self._builtin_range
        self.globals["parimaanam"] = self._builtin_parimaanam
        self.globals["type_of"] = self._builtin_type_of
        self.globals["Sankhya"] = self._builtin_sankhya
        self.globals["Padam"] = self._builtin_padam
        self.globals["Dasamsam"] = self._builtin_dasamsam
        self.globals["__call_method__"] = self._builtin_call_method

    def _builtin_cheppu(self, *args: Any) -> None:
        text = " ".join(self._display(a) for a in args)
        self.stdout.write(text + "\n")
        self.stdout.flush()

    def _builtin_range(self, *args: Any) -> list[int]:
        if len(args) == 1:
            return list(range(int(args[0])))
        if len(args) == 2:
            return list(range(int(args[0]), int(args[1])))
        if len(args) >= 3:
            return list(range(int(args[0]), int(args[1]), int(args[2])))
        return []

    def _builtin_parimaanam(self, val: Any) -> int:
        if isinstance(val, (list, tuple, str, dict)):
            return len(val)
        return 0

    def _builtin_type_of(self, val: Any) -> str:
        if isinstance(val, bool): return "Nijam"
        if isinstance(val, int): return "Sankhya"
        if isinstance(val, float): return "Dasamsam"
        if isinstance(val, str): return "Padam"
        if isinstance(val, list): return "Gumpu"
        if isinstance(val, dict): return "Naksha"
        if isinstance(val, tuple): return "Janta"
        if val is None: return "Shunyam"
        return type(val).__name__

    def _builtin_sankhya(self, val: Any) -> int:
        try:
            return int(val)
        except Exception:
            return 0

    def _builtin_padam(self, val: Any) -> str:
        return self._display(val)

    def _builtin_dasamsam(self, val: Any) -> float:
        try:
            return float(val)
        except Exception:
            return 0.0

    def _builtin_call_method(self, obj: Any, method_name: str, *args: Any) -> Any:
        """Dynamic method dispatch for collections and strings."""
        if isinstance(obj, list):
            if method_name == "map" and args:
                fn = args[0]
                return [self._invoke_callable(fn, [item]) for item in obj]
            if method_name == "filter" and args:
                fn = args[0]
                return [item for item in obj if bool(self._invoke_callable(fn, [item]))]
            if method_name == "reduce" and len(args) >= 2:
                fn, acc = args[0], args[1]
                for item in obj:
                    acc = self._invoke_callable(fn, [acc, item])
                return acc
            if method_name == "cherchu" and args:
                obj.append(args[0])
                return None
            if method_name == "length":
                return len(obj)

        if isinstance(obj, str):
            if method_name == "upper": return obj.upper()
            if method_name == "lower": return obj.lower()
            if method_name == "length": return len(obj)
            if method_name == "contains" and args: return str(args[0]) in obj
            if method_name == "replace" and len(args) >= 2: return obj.replace(str(args[0]), str(args[1]))

        if isinstance(obj, dict):
            if method_name == "keys": return list(obj.keys())
            if method_name == "values": return list(obj.values())

        raise AttributeError(f"Object of type '{type(obj).__name__}' has no method '{method_name}'")

    def _display(self, val: Any) -> str:
        if val is True: return "nijam"
        if val is False: return "abaddham"
        if val is None: return "shunyam"
        if isinstance(val, float) and val == int(val): return str(val)
        return str(val)

    def execute(self, chunk: CodeChunk, initial_locals: Optional[dict[str, Any]] = None) -> Any:
        """Run a compiled bytecode chunk to completion."""
        top_frame = CallFrame(chunk=chunk, ip=0, locals=dict(initial_locals) if initial_locals is not None else {})
        self.frames = [top_frame]
        self.stack.clear()

        while self.frames:
            frame = self.frames[-1]
            if frame.ip >= len(frame.chunk.instructions):
                self.frames.pop()
                continue

            inst = frame.chunk.instructions[frame.ip]
            frame.ip += 1

            op = inst.opcode
            arg = inst.arg

            # ── Stack & Constants ─────────────────────────────────────────────
            if op == OpCode.LOAD_CONST:
                self.stack.append(frame.chunk.constants[arg])

            elif op == OpCode.POP_TOP:
                if self.stack: self.stack.pop()

            elif op == OpCode.DUP_TOP:
                self.stack.append(self.stack[-1])

            elif op == OpCode.ROT_TWO:
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append(a)
                self.stack.append(b)

            # ── Variables & Names ─────────────────────────────────────────────
            elif op == OpCode.LOAD_NAME:
                name = frame.chunk.names[arg]
                if name in frame.locals:
                    self.stack.append(frame.locals[name])
                elif name in self.globals:
                    self.stack.append(self.globals[name])
                else:
                    raise NameError(f"Name '{name}' is not defined (line {inst.line})")

            elif op == OpCode.STORE_NAME:
                name = frame.chunk.names[arg]
                val = self.stack.pop()
                frame.locals[name] = val
                # Also synchronize with globals if top frame
                if len(self.frames) == 1:
                    self.globals[name] = val

            elif op == OpCode.LOAD_GLOBAL:
                name = frame.chunk.names[arg]
                if name in self.globals:
                    self.stack.append(self.globals[name])
                else:
                    raise NameError(f"Global '{name}' is not defined")

            elif op == OpCode.STORE_GLOBAL:
                name = frame.chunk.names[arg]
                self.globals[name] = self.stack.pop()

            # ── Arithmetic ────────────────────────────────────────────────────
            elif op == OpCode.BINARY_ADD:
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, str) or isinstance(b, str):
                    self.stack.append(self._display(a) + self._display(b))
                elif isinstance(a, list) and isinstance(b, list):
                    self.stack.append(a + b)
                else:
                    self.stack.append(a + b)

            elif op == OpCode.BINARY_SUB:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)

            elif op == OpCode.BINARY_MUL:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)

            elif op == OpCode.BINARY_DIV:
                b = self.stack.pop()
                a = self.stack.pop()
                if b == 0:
                    raise ZeroDivisionError(f"Division by zero at line {inst.line}")
                self.stack.append(a / b)

            elif op == OpCode.BINARY_MOD:
                b = self.stack.pop()
                a = self.stack.pop()
                if b == 0:
                    raise ZeroDivisionError(f"Modulo by zero at line {inst.line}")
                self.stack.append(a % b)

            elif op == OpCode.BINARY_POW:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a ** b)

            elif op == OpCode.UNARY_NEGATIVE:
                self.stack.append(-self.stack.pop())

            elif op == OpCode.UNARY_NOT:
                self.stack.append(not bool(self.stack.pop()))

            # ── Comparison ────────────────────────────────────────────────────
            elif op == OpCode.COMPARE_OP:
                b = self.stack.pop()
                a = self.stack.pop()
                cmp_type = CMP_SYMBOLS[arg] if 0 <= arg < len(CMP_SYMBOLS) else "=="
                match cmp_type:
                    case "==": self.stack.append(a == b)
                    case "!=": self.stack.append(a != b)
                    case "<":  self.stack.append(a < b)
                    case "<=": self.stack.append(a <= b)
                    case ">":  self.stack.append(a > b)
                    case ">=": self.stack.append(a >= b)

            # ── Jumps & Control Flow ──────────────────────────────────────────
            elif op == OpCode.JUMP_ABSOLUTE:
                frame.ip = arg

            elif op == OpCode.JUMP_FORWARD:
                frame.ip += arg

            elif op == OpCode.POP_JUMP_IF_FALSE:
                cond = self.stack.pop()
                if not bool(cond):
                    frame.ip = arg

            elif op == OpCode.POP_JUMP_IF_TRUE:
                cond = self.stack.pop()
                if bool(cond):
                    frame.ip = arg

            elif op == OpCode.JUMP_IF_FALSE_OR_POP:
                if not bool(self.stack[-1]):
                    frame.ip = arg
                else:
                    self.stack.pop()

            elif op == OpCode.JUMP_IF_TRUE_OR_POP:
                if bool(self.stack[-1]):
                    frame.ip = arg
                else:
                    self.stack.pop()

            # ── Iteration ─────────────────────────────────────────────────────
            elif op == OpCode.GET_ITER:
                iterable = self.stack.pop()
                self.stack.append(iter(iterable))

            elif op == OpCode.FOR_ITER:
                iterator = self.stack[-1]
                try:
                    next_val = next(iterator)
                    self.stack.append(next_val)
                except StopIteration:
                    self.stack.pop() # pop iterator
                    frame.ip = arg   # jump past loop

            # ── Collections ───────────────────────────────────────────────────
            elif op == OpCode.BUILD_LIST:
                items = [self.stack.pop() for _ in range(arg)]
                items.reverse()
                self.stack.append(items)

            elif op == OpCode.BUILD_MAP:
                mapping = {}
                pairs = []
                for _ in range(arg):
                    v = self.stack.pop()
                    k = self.stack.pop()
                    pairs.append((k, v))
                pairs.reverse()
                for k, v in pairs:
                    mapping[k] = v
                self.stack.append(mapping)

            elif op == OpCode.BUILD_TUPLE:
                items = [self.stack.pop() for _ in range(arg)]
                items.reverse()
                self.stack.append(tuple(items))

            elif op == OpCode.BINARY_SUBSCR:
                idx = self.stack.pop()
                container = self.stack.pop()
                self.stack.append(container[idx])

            elif op == OpCode.STORE_SUBSCR:
                val = self.stack.pop()
                idx = self.stack.pop()
                container = self.stack.pop()
                container[idx] = val

            # ── Formatting & Printing ─────────────────────────────────────────
            elif op == OpCode.PRINT_EXPR:
                args = [self.stack.pop() for _ in range(arg)]
                args.reverse()
                self._builtin_cheppu(*args)
                self.stack.append(None)


            elif op == OpCode.FORMAT_VALUE:
                val = self.stack.pop()
                self.stack.append(self._display(val))

            elif op == OpCode.BUILD_STRING:
                parts = [self.stack.pop() for _ in range(arg)]
                parts.reverse()
                self.stack.append("".join(parts))

            # ── Functions & Calls ─────────────────────────────────────────────
            elif op == OpCode.MAKE_FUNCTION:
                func_chunk = self.stack.pop()
                fn = VMFunction(chunk=func_chunk, closure=dict(frame.locals))
                self.stack.append(fn)

            elif op == OpCode.CALL_FUNCTION:
                args = [self.stack.pop() for _ in range(arg)]
                args.reverse()
                callee = self.stack.pop()

                if isinstance(callee, VMFunction):
                    new_locals = dict(callee.closure)
                    for param_name, param_val in zip(callee.chunk.argnames, args):
                        new_locals[param_name] = param_val
                    new_frame = CallFrame(chunk=callee.chunk, ip=0, locals=new_locals)
                    self.frames.append(new_frame)
                elif callable(callee):
                    res = callee(*args)
                    self.stack.append(res)
                else:
                    raise TypeError(f"'{type(callee).__name__}' object is not callable (line {inst.line})")

            elif op == OpCode.RETURN_VALUE:
                ret_val = self.stack.pop() if self.stack else None
                self.frames.pop()
                if self.frames:
                    self.stack.append(ret_val)
                else:
                    return ret_val

        return self.stack[-1] if self.stack else None

    def _invoke_callable(self, callee: Any, args: list[Any]) -> Any:
        """Invoke a callable (VMFunction or Python function) inside the VM synchronously."""
        if callable(callee) and not isinstance(callee, VMFunction):
            return callee(*args)

        if isinstance(callee, VMFunction):
            sub_vm = AkashaVM(stdout=self.stdout)
            sub_vm.globals = self.globals
            new_locals = dict(callee.closure)
            for param_name, param_val in zip(callee.chunk.argnames, args):
                new_locals[param_name] = param_val
            return sub_vm.execute(callee.chunk, initial_locals=new_locals)

        raise TypeError(f"Object '{callee}' is not callable")
