#!/usr/bin/env python3
"""
Akasha Programming Language — CLI
=================================

Commands:
  akasha run   <file.akasha>   Run an Akasha source file
  akasha check <file.akasha>   Parse and type-check without running
  akasha repl                  Start interactive REPL
  akasha version               Show version information
  akasha help                  Show help

Usage:
  python -m akasha.cli.astra run hello.akasha
  python akasha.py run hello.akasha
"""

from __future__ import annotations
import sys
import os
import traceback
from pathlib import Path

# Allow running as 'python cli/astra.py' from the project root
_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from akasha.compiler.lexer.lexer   import Lexer,  LexerError
from akasha.compiler.parser.parser import Parser, ParseError
from akasha.compiler.interpreter.interpreter import Interpreter
from akasha.compiler.interpreter.values import (
    AkashaRuntimeError, ReturnSignal, _to_display_str
)

VERSION = "0.1.0"
CODENAME = "Akasha"
TAGLINE  = "The Telugu-inspired programming language"

BANNER = f"""
   █████╗ ██╗  ██╗ █████╗ ███████╗██╗  ██╗ █████╗ 
  ██╔══██╗██║ ██╔╝██╔══██╗██╔════╝██║  ██║██╔══██╗
  ███████║█████═╝ ███████║███████╗███████║███████║
  ██╔══██║██╔═██╗ ██╔══██║╚════██║██╔══██║██╔══██║
  ██║  ██║██║ ╚██╗██║  ██║███████║██║  ██║██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝

  {CODENAME} v{VERSION} — {TAGLINE}
  Type 'help' for commands, 'exit' to quit.
"""

HELP_TEXT = f"""
Akasha Programming Language v{VERSION}

USAGE:
  akasha <command> [arguments]

COMMANDS:
  run     <file.akasha>  Execute an Akasha source file
  compile <file.akasha>  Compile source into bytecode (.akb)
  check   <file.akasha>  Parse and check without running
  repl                   Start interactive REPL
  ide                    Launch native Desktop Code Editor (PC IDE)
  web     [--port 8080]  Start interactive Web Compiler & Playground
  version                Show version information
  help                   Show this help message



EXAMPLES:
  akasha run hello.akasha
  akasha repl
  akasha check myprogram.akasha

FILE EXTENSION:
  .akasha, .aka  (e.g., hello.akasha)

LANGUAGE QUICK REFERENCE:
  cheppu("Hello, World!")             -- print
  viluva x = 42                        -- variable
  sthiram PI = 3.14159                 -- constant
  okavela x > 10 {{ cheppu("big") }}    -- if
  prathi i lo 1..5 {{ cheppu(i) }}      -- for loop
  karyam add(a, b) {{ phalitham a+b }}  -- function

DOCUMENTATION:
  README.md in the repository
"""


def _read_file(path: str) -> str:
    """Read an Akasha source file with helpful error messages."""
    p = Path(path)
    if not p.exists():
        print(f"\nError: File not found: '{path}'", file=sys.stderr)
        print(f"  Check that the file path is correct.", file=sys.stderr)
        sys.exit(1)
    if not p.suffix in (".akasha", ".aka", ".teja", ".tj"):
        print(f"\nWarning: File '{path}' does not have a .akasha extension.", file=sys.stderr)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"\nError: File '{path}' is not valid UTF-8 text.", file=sys.stderr)
        sys.exit(1)


def _run_source(source: str, filename: str, interpreter: Interpreter) -> None:
    """Lex → Parse → Interpret an Akasha source string."""
    # ── Lex ──────────────────────────────────────────────────────────────
    try:
        lexer  = Lexer(source, filename)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # ── Parse ─────────────────────────────────────────────────────────────
    try:
        parser  = Parser(tokens)
        program = parser.parse()
    except ParseError as e:
        print(str(e), file=sys.stderr)
        lines = source.splitlines()
        if e.token.line > 0 and e.token.line <= len(lines):
            lineno  = e.token.line
            line    = lines[lineno - 1]
            pointer = " " * (e.token.col - 1) + "^" * max(1, len(e.token.value))
            print(f"  {lineno:4} | {line}", file=sys.stderr)
            print(f"       | {pointer}", file=sys.stderr)
        sys.exit(1)

    # ── Interpret ─────────────────────────────────────────────────────────
    try:
        interpreter.execute(program)
    except AkashaRuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except ReturnSignal:
        pass   # top-level return is fine
    except KeyboardInterrupt:
        print("\n\nInterrupted.", file=sys.stderr)
        sys.exit(130)


def cmd_run(args: list[str]) -> None:
    """akasha run <file.akasha | file.akb>"""
    if not args:
        print("Error: 'run' requires a file argument.\n"
              "  Usage: akasha run <file.akasha | file.akb>", file=sys.stderr)
        sys.exit(1)
    filename = args[0]
    p = Path(filename)
    if not p.exists():
        print(f"\nError: File not found: '{filename}'", file=sys.stderr)
        sys.exit(1)

    # If bytecode file (.akb), run directly in the Akasha VM
    if p.suffix.lower() == ".akb":
        from akasha.compiler.bytecode.serializer import load_bytecode_file
        from akasha.runtime.vm import AkashaVM
        try:
            chunk = load_bytecode_file(str(p))
            vm = AkashaVM()
            vm.execute(chunk)
        except Exception as e:
            print(f"\nVM Runtime Error:\n  {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Source file (.akasha)
    source = _read_file(filename)
    interp = Interpreter()
    _run_source(source, filename, interp)


def cmd_compile(args: list[str]) -> None:
    """akasha compile <file.akasha> [-o out.akb] [--dis]"""
    from akasha.cli.compiler_cli import compile_file
    import argparse
    parser = argparse.ArgumentParser(prog="akasha compile", description="Compile Akasha source to .akb bytecode")
    parser.add_argument("source", help="Akasha source file (.akasha)")
    parser.add_argument("-o", "--output", help="Output bytecode file path")
    parser.add_argument("-d", "--dis", action="store_true", help="Print disassembly")
    parser.add_argument("-r", "--run", action="store_true", help="Run after compilation")
    parsed_args = parser.parse_args(args)

    code = compile_file(
        source_path=parsed_args.source,
        output_path=parsed_args.output,
        dis_only=parsed_args.dis,
        run_after=parsed_args.run
    )
    if code != 0:
        sys.exit(code)



def cmd_check(args: list[str]) -> None:
    """akasha check <file.akasha> — parse only"""
    if not args:
        print("Error: 'check' requires a file argument.", file=sys.stderr)
        sys.exit(1)
    filename = args[0]
    source   = _read_file(filename)
    try:
        lexer  = Lexer(source, filename)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        parser.parse()
        print(f"  OK — '{filename}' parsed successfully (no syntax errors).")
    except (LexerError, ParseError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def cmd_repl() -> None:
    """akasha repl — interactive Read-Eval-Print Loop"""
    print(BANNER)
    interp = Interpreter()
    history: list[str] = []

    while True:
        try:
            line = input("akasha> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNamaste! (goodbye)")
            break

        if not line:
            continue

        if line in ("exit", "quit", "bayatapadu"):
            print("Namaste! (goodbye)")
            break

        if line == "help":
            print(HELP_TEXT)
            continue

        if line == "version":
            print(f"Akasha v{VERSION}")
            continue

        if line == "history":
            for i, h in enumerate(history[-20:], 1):
                print(f"  {i:3}: {h}")
            continue

        history.append(line)

        # Support multi-line input: if line ends with '{', keep reading
        if line.endswith("{"):
            while True:
                try:
                    more = input("...   ")
                    line += "\n" + more
                    if more.strip() == "}":
                        break
                except (EOFError, KeyboardInterrupt):
                    break

        try:
            lexer  = Lexer(line, "<repl>")
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            program = parser.parse()

            # If it's a single expression, print the result
            from akasha.compiler.ast_nodes.nodes import ExprStatement
            if (len(program.body) == 1 and
                    isinstance(program.body[0], ExprStatement)):
                result = interp.execute_expression(program.body[0].expr)
                from akasha.compiler.interpreter.values import SHUNYAM as _SHUNYAM
                if result is not _SHUNYAM:
                    print(f"  => {_to_display_str(result)}")
            else:
                interp.execute(program)

        except LexerError as e:
            print(f"Lexer Error: {e}", file=sys.stderr)
        except ParseError as e:
            print(f"Parse Error: {e}", file=sys.stderr)
        except AkashaRuntimeError as e:
            print(f"Runtime Error: {e}", file=sys.stderr)
        except ReturnSignal as r:
            if r.value is not None:
                print(f"  => {_to_display_str(r.value)}")
        except Exception as e:
            print(f"Internal Error: {e}", file=sys.stderr)
            if os.environ.get("AKASHA_DEBUG"):
                traceback.print_exc()


def cmd_version() -> None:
    """akasha version"""
    print(f"""
Akasha Programming Language
  Version  : {VERSION}
  Codename : {CODENAME}
  Runtime  : Python {sys.version.split()[0]}
  Platform : {sys.platform}
  {TAGLINE}
""")


def cmd_web(args: list[str]) -> None:
    """akasha web [--port 8080] [--host 127.0.0.1] [--open]"""
    import argparse
    from akasha.web.server import start_server

    parser = argparse.ArgumentParser(prog="akasha web", description="Start Akasha Web Compiler")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port number (default: 8080)")
    parser.add_argument("--open", "-o", action="store_true", help="Automatically open browser")
    parsed_args = parser.parse_args(args)

    start_server(host=parsed_args.host, port=parsed_args.port, open_browser=parsed_args.open)


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print(HELP_TEXT)
        sys.exit(0)

    command = args[0]
    rest    = args[1:]

    match command:
        case "run":     cmd_run(rest)
        case "compile": cmd_compile(rest)
        case "check":   cmd_check(rest)
        case "repl":    cmd_repl()
        case "ide":
            from akasha.ide.app import launch_ide
            launch_ide()
        case "web":     cmd_web(rest)
        case "version": cmd_version()
        case "help":    print(HELP_TEXT)
        case _:
            # Try running as a file directly: 'akasha hello.akasha' or 'akasha hello.akb'
            if command.endswith((".akasha", ".aka", ".akb", ".teja", ".tj")) and Path(command).exists():
                cmd_run([command] + rest)
            else:
                print(f"\nError: Unknown command '{command}'", file=sys.stderr)
                print(f"  Run 'akasha help' for available commands.", file=sys.stderr)
                sys.exit(1)





if __name__ == "__main__":
    main()
