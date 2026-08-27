"""
Akasha Studio — Desktop Application Local Backend Server
=========================================================

Provides local HTTP/JSON API endpoints for code execution, bytecode
compilation, workspace file management, and syntax analysis.
"""

from __future__ import annotations
import sys
import io
import time
import json
import socket
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

# Ensure project root is in sys.path
_STUDIO_DIR = Path(__file__).resolve().parent
_ROOT = _STUDIO_DIR.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from akasha.compiler.lexer.lexer import Lexer, LexerError
from akasha.compiler.parser.parser import Parser, ParseError
from akasha.compiler.bytecode.compiler import BytecodeCompiler
from akasha.compiler.bytecode.opcodes import OpCode
from akasha.compiler.bytecode.serializer import save_bytecode_file
from akasha.compiler.interpreter.interpreter import Interpreter
from akasha.compiler.interpreter.values import AkashaRuntimeError, ReturnSignal, _to_display_str

DEFAULT_WORKSPACE = _ROOT / "examples"


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def execute_code(source: str) -> dict:
    start_time = time.perf_counter()
    stdout_buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buf

    try:
        lexer = Lexer(source, "<studio>")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        interp = Interpreter()
        interp.execute(program)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": True,
            "output": stdout_buf.getvalue(),
            "error": None,
            "execution_time_ms": elapsed_ms,
        }
    except LexerError as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {"phase": "Lexer", "message": str(e)},
            "execution_time_ms": elapsed_ms,
        }
    except ParseError as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {"phase": "Parser", "message": str(e)},
            "execution_time_ms": elapsed_ms,
        }
    except AkashaRuntimeError as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {"phase": "Runtime", "message": str(e)},
            "execution_time_ms": elapsed_ms,
        }
    except ReturnSignal as r:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        out = stdout_buf.getvalue()
        if r.value is not None:
            out += f"\n[Return value]: {_to_display_str(r.value)}"
        return {
            "success": True,
            "output": out,
            "error": None,
            "execution_time_ms": elapsed_ms,
        }
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {"phase": "System", "message": str(e)},
            "execution_time_ms": elapsed_ms,
        }
    finally:
        sys.stdout = old_stdout


def disassemble_bytecode(source: str) -> dict:
    start_time = time.perf_counter()
    try:
        lexer = Lexer(source, "<studio>").tokenize()
        program = Parser(lexer).parse()
        compiler = BytecodeCompiler(filename="<studio>")
        chunk = compiler.compile(program)
        
        instructions = []
        for idx, instr in enumerate(chunk.instructions):
            opcode_name = instr.opcode.name
            arg_repr = ""
            if instr.arg is not None:
                if instr.opcode == OpCode.LOAD_CONST:
                    arg_repr = repr(chunk.constants[instr.arg]) if instr.arg < len(chunk.constants) else str(instr.arg)
                elif instr.opcode in (OpCode.LOAD_FAST, OpCode.STORE_FAST):
                    arg_repr = chunk.locals[instr.arg] if instr.arg < len(chunk.locals) else str(instr.arg)
                elif instr.opcode in (OpCode.LOAD_GLOBAL, OpCode.STORE_GLOBAL):
                    arg_repr = chunk.names[instr.arg] if instr.arg < len(chunk.names) else str(instr.arg)
                else:
                    arg_repr = str(instr.arg)

            instructions.append({
                "offset": idx,
                "opcode": opcode_name,
                "arg": instr.arg,
                "arg_repr": arg_repr,
                "line": instr.line
            })

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": True,
            "instructions": instructions,
            "constants": [repr(c) for c in chunk.constants],
            "locals": chunk.locals,
            "names": chunk.names,
            "time_ms": elapsed_ms
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_workspace_files() -> list[dict]:
    files = []
    if DEFAULT_WORKSPACE.exists():
        for item in sorted(DEFAULT_WORKSPACE.glob("*.akasha")):
            files.append({
                "name": item.name,
                "path": str(item),
                "size": item.stat().st_size
            })
    return files


class StudioRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(_STUDIO_DIR), **kwargs)

    def _set_json_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_json_headers(200)

    def do_GET(self) -> None:
        if self.path == "/api/workspace/files":
            files = list_workspace_files()
            self._set_json_headers(200)
            self.wfile.write(json.dumps({"files": files}).encode("utf-8"))
            return

        if self.path.startswith("/api/file/read"):
            # Query param: ?path=...
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            file_path = query.get("path", [""])[0]
            try:
                target = Path(file_path)
                if target.exists() and target.is_file():
                    content = target.read_text(encoding="utf-8")
                    self._set_json_headers(200)
                    self.wfile.write(json.dumps({"success": True, "content": content, "name": target.name}).encode("utf-8"))
                else:
                    self._set_json_headers(404)
                    self.wfile.write(json.dumps({"success": False, "error": "File not found"}).encode("utf-8"))
            except Exception as e:
                self._set_json_headers(500)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # Fallback to static files
        super().do_GET()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw_data = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"

        try:
            body = json.loads(raw_data)
        except json.JSONDecodeError:
            self._set_json_headers(400)
            self.wfile.write(json.dumps({"success": False, "error": "Invalid JSON"}).encode("utf-8"))
            return

        if self.path == "/api/run":
            code = body.get("code", "")
            result = execute_code(code)
            self._set_json_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        if self.path == "/api/disassemble":
            code = body.get("code", "")
            result = disassemble_bytecode(code)
            self._set_json_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        if self.path == "/api/check":
            code = body.get("code", "")
            try:
                tokens = Lexer(code, "<studio>").tokenize()
                Parser(tokens).parse()
                self._set_json_headers(200)
                self.wfile.write(json.dumps({"success": True, "message": "Syntax valid"}).encode("utf-8"))
            except Exception as e:
                self._set_json_headers(200)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/file/save":
            file_path = body.get("path", "")
            content = body.get("content", "")
            try:
                target = Path(file_path) if file_path else (DEFAULT_WORKSPACE / body.get("name", "untitled.akasha"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                self._set_json_headers(200)
                self.wfile.write(json.dumps({"success": True, "path": str(target), "name": target.name}).encode("utf-8"))
            except Exception as e:
                self._set_json_headers(500)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        self._set_json_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def start_server(port: int = 9100) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), StudioRequestHandler)
    return server


if __name__ == "__main__":
    port = 9100
    server = start_server(port)
    print(f"Akasha Studio Server running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.shutdown()
