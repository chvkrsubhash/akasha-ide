#!/usr/bin/env python3
"""
akashac — The Akasha Bytecode Compiler CLI
==========================================

Compiles Akasha source files (.akasha) into standalone executable bytecode (.akb).

Usage:
  akashac hello.akasha                  # Compiles to hello.akb
  akashac hello.akasha -o myprog.akb    # Custom output name
  akashac hello.akasha --dis            # Disassemble & view bytecode instructions
  akashac hello.akasha --run            # Compile & immediately run in Akasha VM
  akashac hello.akasha --check          # Validate syntax only
"""

from __future__ import annotations
import sys
import os
import argparse
from pathlib import Path

# Ensure project root is in sys.path
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from akasha.compiler.lexer.lexer import Lexer, LexerError
from akasha.compiler.parser.parser import Parser, ParseError
from akasha.compiler.bytecode.compiler import BytecodeCompiler
from akasha.compiler.bytecode.serializer import save_bytecode_file, disassemble
from akasha.runtime.vm import AkashaVM


def compile_file(source_path: str, output_path: str | None = None, dis_only: bool = False, run_after: bool = False, check_only: bool = False) -> int:
    """Compile an Akasha source file to a .akb bytecode file or disassemble/run it."""
    path = Path(source_path)
    if not path.exists():
        print(f"akashac: error: File not found: '{source_path}'", file=sys.stderr)
        return 1

    try:
        source_code = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"akashac: error reading '{source_path}': {e}", file=sys.stderr)
        return 1

    # 1. Lexing
    try:
        lexer = Lexer(source_code, filename=str(path))
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"akashac: [Lexer Error] {e}", file=sys.stderr)
        return 1

    # 2. Parsing
    try:
        parser = Parser(tokens)
        program = parser.parse()
    except ParseError as e:
        print(f"akashac: [Parse Error] {e}", file=sys.stderr)
        lines = source_code.splitlines()
        if e.token and 0 < e.token.line <= len(lines):
            lineno = e.token.line
            print(f"  {lineno:4} | {lines[lineno - 1]}", file=sys.stderr)
            pointer = " " * (e.token.col - 1) + "^" * max(1, len(e.token.value))
            print(f"       | {pointer}", file=sys.stderr)
        return 1

    if check_only:
        print(f"akashac: syntax OK - '{source_path}'")
        return 0

    # 3. Bytecode Compilation
    try:
        compiler = BytecodeCompiler(filename=str(path))
        chunk = compiler.compile(program)
    except Exception as e:
        print(f"akashac: [Compilation Error] {e}", file=sys.stderr)
        return 1

    # 4. Disassembly mode
    if dis_only:
        print(disassemble(chunk))
        return 0

    # 5. Output bytecode binary
    if not output_path:
        output_path = str(path.with_suffix(".akb"))

    try:
        save_bytecode_file(chunk, output_path)
        print(f"akashac: compiled '{source_path}' -> '{output_path}' ({len(chunk.instructions)} instructions)")
    except Exception as e:
        print(f"akashac: error saving bytecode to '{output_path}': {e}", file=sys.stderr)
        return 1

    # 6. Run if requested
    if run_after:
        print(f"--- Running in Akasha VM ---")
        vm = AkashaVM()
        vm.execute(chunk)

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="akashac",
        description="Akasha Bytecode Compiler — Compile Akasha source into binary bytecode (.akb)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  akashac hello.akasha                  # Produces hello.akb
  akashac -o app.akb hello.akasha       # Custom binary name
  akashac --dis hello.akasha            # View bytecode disassembly
  akashac --run hello.akasha            # Compile and run
        """
    )
    parser.add_argument("source", help="Akasha source file to compile (.akasha)")
    parser.add_argument("-o", "--output", help="Output compiled bytecode file path (.akb)")
    parser.add_argument("-d", "--dis", action="store_true", help="Disassemble and print bytecode instructions")
    parser.add_argument("-r", "--run", action="store_true", help="Immediately execute compiled bytecode in Akasha VM")
    parser.add_argument("-c", "--check", action="store_true", help="Validate syntax without emitting bytecode")
    parser.add_argument("-v", "--version", action="version", version="akashac 0.1.0")

    args = parser.parse_args()
    code = compile_file(
        source_path=args.source,
        output_path=args.output,
        dis_only=args.dis,
        run_after=args.run,
        check_only=args.check
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
