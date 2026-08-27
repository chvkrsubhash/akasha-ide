"""
Akasha Bytecode — CodeChunk and Binary Serialization (.akb)
============================================================

Manages bytecode chunks, disassembly, and binary file I/O.
"""

from __future__ import annotations
import pickle
import struct
import io
from dataclasses import dataclass, field
from typing import Any
from .opcodes import OpCode, Instruction, CMP_SYMBOLS

MAGIC_HEADER = b"AKB\x01\x00\x00\x00"


@dataclass
class CodeChunk:
    """A compiled unit of bytecode (e.g. top-level module or a function body)."""
    name: str = "<module>"
    filename: str = "<unknown>"
    argnames: list[str] = field(default_factory=list)
    constants: list[Any] = field(default_factory=list)
    names: list[str] = field(default_factory=list)
    instructions: list[Instruction] = field(default_factory=list)

    def add_constant(self, value: Any) -> int:
        # Check if constant already exists (for ints, floats, strings, bools, None)
        for i, c in enumerate(self.constants):
            if type(c) is type(value) and c == value:
                return i
        self.constants.append(value)
        return len(self.constants) - 1

    def add_name(self, name: str) -> int:
        for i, n in enumerate(self.names):
            if n == name:
                return i
        self.names.append(name)
        return len(self.names) - 1

    def emit(self, opcode: OpCode, arg: int = 0, argval: Any = None, line: int = 0, col: int = 0) -> int:
        idx = len(self.instructions)
        self.instructions.append(Instruction(opcode, arg, argval, line, col))
        return idx

    def patch_jump(self, instruction_index: int, target_index: int) -> None:
        """Patch a jump instruction's target destination."""
        self.instructions[instruction_index].arg = target_index
        self.instructions[instruction_index].argval = f"to {target_index}"


def disassemble(chunk: CodeChunk, indent: str = "") -> str:
    """Produce human-readable disassembly text for a code chunk."""
    lines: list[str] = []
    lines.append(f"{indent}Disassembly of {chunk.name} ({chunk.filename}):")
    if chunk.argnames:
        lines.append(f"{indent}  Arguments: {', '.join(chunk.argnames)}")
    if chunk.constants:
        lines.append(f"{indent}  Constants: {chunk.constants}")
    if chunk.names:
        lines.append(f"{indent}  Names:     {chunk.names}")
    lines.append(f"{indent}  Instructions:")

    for idx, inst in enumerate(chunk.instructions):
        line_info = f"{inst.line:>4}" if inst.line else "    "
        op_name = inst.opcode.name
        arg_str = ""
        extra = ""

        if inst.opcode == OpCode.LOAD_CONST:
            val = chunk.constants[inst.arg] if 0 <= inst.arg < len(chunk.constants) else None
            extra = f" ({val!r})"
            arg_str = f"{inst.arg}"
        elif inst.opcode in (OpCode.LOAD_NAME, OpCode.STORE_NAME, OpCode.LOAD_GLOBAL, OpCode.STORE_GLOBAL):
            name = chunk.names[inst.arg] if 0 <= inst.arg < len(chunk.names) else "?"
            extra = f" ({name})"
            arg_str = f"{inst.arg}"
        elif inst.opcode == OpCode.COMPARE_OP:
            symbol = CMP_SYMBOLS[inst.arg] if 0 <= inst.arg < len(CMP_SYMBOLS) else "?"
            extra = f" ({symbol})"
            arg_str = f"{inst.arg}"
        elif inst.opcode in (OpCode.POP_JUMP_IF_FALSE, OpCode.POP_JUMP_IF_TRUE, OpCode.JUMP_ABSOLUTE, OpCode.FOR_ITER):
            extra = f" (to {inst.arg})"
            arg_str = f"{inst.arg}"
        elif inst.arg != 0:
            arg_str = f"{inst.arg}"

        lines.append(f"{indent}  {line_info}  {idx:>4}  {op_name:<22} {arg_str:>4}{extra}")

    # Also disassemble nested function constants
    for c in chunk.constants:
        if isinstance(c, CodeChunk):
            lines.append("")
            lines.append(disassemble(c, indent=indent + "    "))

    return "\n".join(lines)


def serialize_to_bytes(chunk: CodeChunk) -> bytes:
    """Serialize a CodeChunk into a binary byte string."""
    buf = io.BytesIO()
    buf.write(MAGIC_HEADER)
    payload = pickle.dumps(chunk, protocol=5)
    buf.write(struct.pack("<I", len(payload)))
    buf.write(payload)
    return buf.getvalue()


def deserialize_from_bytes(data: bytes) -> CodeChunk:
    """Deserialize a binary byte string into a CodeChunk."""
    if not data.startswith(MAGIC_HEADER):
        raise ValueError("Invalid Akasha bytecode file: missing or invalid magic header")
    header_len = len(MAGIC_HEADER)
    payload_len = struct.unpack("<I", data[header_len:header_len + 4])[0]
    payload = data[header_len + 4: header_len + 4 + payload_len]
    chunk = pickle.loads(payload)
    if not isinstance(chunk, CodeChunk):
        raise TypeError("Deserialized object is not an Akasha CodeChunk")
    return chunk


def save_bytecode_file(chunk: CodeChunk, filepath: str) -> None:
    """Save compiled bytecode to a .akb file on disk."""
    data = serialize_to_bytes(chunk)
    with open(filepath, "wb") as f:
        f.write(data)


def load_bytecode_file(filepath: str) -> CodeChunk:
    """Load compiled bytecode from a .akb file on disk."""
    with open(filepath, "rb") as f:
        data = f.read()
    return deserialize_from_bytes(data)
