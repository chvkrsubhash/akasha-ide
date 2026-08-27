"""
Akasha Web Compiler & API Server
================================

Provides HTTP JSON API endpoints for:
  - Code execution (/api/run)
  - Syntax checking (/api/check)
  - Token stream inspection (/api/tokens)
  - AST visualization (/api/ast)
  - Examples catalogue (/api/examples)
  - Static file serving (HTML/CSS/JS)
"""

from __future__ import annotations
import io
import sys
import os
import json
import time
import dataclasses
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from akasha.compiler.lexer.lexer import Lexer, LexerError
from akasha.compiler.parser.parser import Parser, ParseError
from akasha.compiler.interpreter.interpreter import Interpreter
from akasha.compiler.interpreter.values import (
    AkashaRuntimeError, ReturnSignal, _to_display_str
)
from akasha.compiler.ast_nodes.nodes import Node

STATIC_DIR = _HERE / "static"


# ── Built-in Examples ─────────────────────────────────────────────────────────

EXAMPLES: list[dict[str, str]] = [
    {
        "id": "hello_world",
        "title": "01. Hello World",
        "category": "Basics",
        "description": "The simplest Akasha program printing greetings",
        "code": """-- Hello World in Akasha
cheppu("Namaste, Akasha!")
cheppu("Welcome to the Telugu-inspired programming language.")
"""
    },
    {
        "id": "variables",
        "title": "02. Variables & Constants",
        "category": "Basics",
        "description": "Declaring mutable variables, constants, types, and formatted strings",
        "code": """-- Variables (viluva) and Constants (sthiram)
viluva peru = "Subhash"
viluva vayasu = 22
sthiram DESHAM = "India"
sthiram PI = 3.14159

cheppu(f"Peru: {peru}, Vayasu: {vayasu}")
cheppu(f"Desham: {DESHAM}, PI: {PI}")

-- Arithmetic operations
viluva a = 20
viluva b = 6
cheppu(f"a + b = {a + b}")
cheppu(f"a - b = {a - b}")
cheppu(f"a * b = {a * b}")
cheppu(f"a / b = {a / b}")
cheppu(f"a % b = {a % b}")
cheppu(f"a ** b = {a ** b}")
"""
    },
    {
        "id": "conditions",
        "title": "03. Conditionals & Match",
        "category": "Control Flow",
        "description": "Branching with okavela, mariyu, lekapothe, and pattern matching (tirugu)",
        "code": """-- Conditional Branching
viluva marks = 88

okavela marks >= 90 {
    cheppu("Grade: A+ (Uttamam)")
} mariyu marks >= 80 {
    cheppu("Grade: A (Baga undi)")
} mariyu marks >= 60 {
    cheppu("Grade: B (Paravaledu)")
} lekapothe {
    cheppu("Grade: Needs improvement")
}

-- Pattern Matching with 'tirugu'
viluva rangu = "pachcha"

tirugu rangu {
    sthithi "erra"    => cheppu("Selected Red (Erra)")
    sthithi "pachcha" => cheppu("Selected Green (Pachcha)")
    sthithi "neelam"  => cheppu("Selected Blue (Neelam)")
    default           => cheppu("Unknown Color")
}
"""
    },
    {
        "id": "functions",
        "title": "04. Functions & Recursion",
        "category": "Functions",
        "description": "Defining functions with karyam, default parameters, recursion, and closures",
        "code": """-- Function definition with return (phalitham)
karyam kalupu(a: Sankhya, b: Sankhya): Sankhya {
    phalitham a + b
}

cheppu(f"10 + 32 = {kalupu(10, 32)}")

-- Recursive Factorial
karyam factorial(n: Sankhya): Sankhya {
    okavela n <= 1 {
        phalitham 1
    }
    phalitham n * factorial(n - 1)
}

cheppu(f"5! = {factorial(5)}")
cheppu(f"10! = {factorial(10)}")

-- Recursive Fibonacci
karyam fib(n: Sankhya): Sankhya {
    okavela n <= 1 { phalitham n }
    phalitham fib(n - 1) + fib(n - 2)
}

cheppu("Fibonacci sequence (0..9):")
prathi i lo 0..10 {
    cheppu(f"  fib({i}) = {fib(i)}")
}
"""
    },
    {
        "id": "loops",
        "title": "05. Loops & Iteration",
        "category": "Control Flow",
        "description": "for-each (prathi..lo), ranges, while (alaa), infinite loop with break (aapu)",
        "code": """-- For-each loop over array
viluva pandlu = ["manga", "arati", "nimma", "jama"]
cheppu("Pandlu:")
prathi p lo pandlu {
    cheppu(f"  - {p}")
}

-- Range loop (1..5)
cheppu("Counting 1 to 5:")
prathi i lo 1..6 {
    cheppu(f"  Number {i}")
}

-- While loop with 'alaa'
viluva count = 1
alaa count <= 3 {
    cheppu(f"  While count: {count}")
    count = count + 1
}

-- Loop with break (aapu) & continue (konasaginchu)
cheppu("Odd numbers only (1..10):")
prathi n lo 1..11 {
    okavela n % 2 == 0 {
        konasaginchu
    }
    cheppu(f"  Odd: {n}")
}
"""
    },
    {
        "id": "closures_and_arrays",
        "title": "06. Closures & Array Methods",
        "category": "Advanced",
        "description": "Anonymous functions with muppu, map, filter, reduce pipelines",
        "code": """-- Closures (muppu) & Functional Programming
viluva numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

-- Map: double every number
viluva doubled = numbers.map(muppu(x) => x * 2)
cheppu(f"Doubled: {doubled}")

-- Filter: only even numbers
viluva evens = numbers.filter(muppu(x) => x % 2 == 0)
cheppu(f"Evens: {evens}")

-- Reduce: sum of elements
viluva sum = numbers.reduce(muppu(acc, x) => acc + x, 0)
cheppu(f"Sum: {sum}")

-- Function returning closure (adder factory)
karyam make_multiplier(factor) {
    phalitham muppu(x) => x * factor
}

viluva triple = make_multiplier(3)
cheppu(f"triple(9) = {triple(9)}")
"""
    },
    {
        "id": "bubble_sort",
        "title": "07. Bubble Sort Algorithm",
        "category": "Algorithms",
        "description": "Implementing classic Bubble Sort in Akasha",
        "code": """-- Bubble Sort Algorithm in Akasha
karyam bubble_sort(arr) {
    viluva n = parimaanam(arr)
    prathi i lo 0..n {
        prathi j lo 0..(n - i - 1) {
            okavela arr[j] > arr[j + 1] {
                viluva temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
            }
        }
    }
    phalitham arr
}

viluva list_data = [64, 34, 25, 12, 22, 11, 90]
cheppu(f"Before Sorting: {list_data}")
viluva sorted_data = bubble_sort(list_data)
cheppu(f"After Sorting:  {sorted_data}")
"""
    },
    {
        "id": "showcase",
        "title": "08. Complete Showcase",
        "category": "Showcase",
        "description": "Comprehensive program demonstrating language syntax and features",
        "code": """--- Comprehensive Akasha Showcase ---

cheppu("=== Akasha Language v0.1 Showcase ===")
cheppu("")

-- 1. Variables & Types
viluva name = "Akasha"
viluva version = 1
viluva stable = nijam
viluva pi_approx = 3.14159

cheppu(f"Language: {name} v{version}")
cheppu(f"Stable: {stable}, Pi: {pi_approx}")
cheppu("")

-- 2. FizzBuzz in Akasha
karyam fizzbuzz(n: Sankhya): Padam {
    okavela n % 15 == 0 {
        phalitham "FizzBuzz"
    } mariyu n % 3 == 0 {
        phalitham "Fizz"
    } mariyu n % 5 == 0 {
        phalitham "Buzz"
    } lekapothe {
        phalitham Padam(n)
    }
}

cheppu("FizzBuzz (1..15):")
prathi i lo 1..16 {
    cheppu(f"  {i}: {fizzbuzz(i)}")
}
cheppu("")

-- 3. String Methods
viluva msg = "Namaste, Akasha!"
cheppu(f"Original: {msg}")
cheppu(f"Upper:    {msg.upper()}")
cheppu(f"Lower:    {msg.lower()}")
cheppu(f"Length:   {msg.length()}")
cheppu(f"Contains: {msg.contains('Akasha')}")

cheppu("")
cheppu("=== Execution Finished ===")
"""
    }
]


# ── AST Serializer ────────────────────────────────────────────────────────────

def ast_to_dict(node: Any) -> Any:
    """Recursively convert an AST node / dataclass to a JSON-serializable dict."""
    if node is None:
        return None
    if isinstance(node, (int, float, str, bool)):
        return node
    if isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    if isinstance(node, tuple):
        return [ast_to_dict(item) for item in node]
    if isinstance(node, dict):
        return {str(k): ast_to_dict(v) for k, v in node.items()}

    if dataclasses.is_dataclass(node):
        result: dict[str, Any] = {
            "_type": node.__class__.__name__,
        }
        for f in dataclasses.fields(node):
            val = getattr(node, f.name)
            result[f.name] = ast_to_dict(val)
        return result

    return str(node)


# ── Core API Handlers ─────────────────────────────────────────────────────────

def run_code(source: str, filename: str = "<web>") -> dict[str, Any]:
    """Execute Akasha source code and return execution outcome."""
    start_time = time.perf_counter()
    stdout_buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buf

    try:
        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        interp = Interpreter()
        interp.execute(program)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        output = stdout_buf.getvalue()
        return {
            "success": True,
            "output": output,
            "error": None,
            "execution_time_ms": elapsed_ms,
            "tokens_count": len(tokens),
            "statements_count": len(program.body),
        }
    except LexerError as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {
                "phase": "Lexer",
                "message": str(e),
                "line": getattr(e, "line", 0),
                "col": getattr(e, "col", 0),
            },
            "execution_time_ms": elapsed_ms,
        }
    except ParseError as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {
                "phase": "Parser",
                "message": str(e),
                "line": e.token.line if e.token else 0,
                "col": e.token.col if e.token else 0,
            },
            "execution_time_ms": elapsed_ms,
        }
    except AkashaRuntimeError as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {
                "phase": "Runtime",
                "message": str(e),
                "line": getattr(e, "line", 0),
                "col": getattr(e, "col", 0),
            },
            "execution_time_ms": elapsed_ms,
        }
    except ReturnSignal as r:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        output = stdout_buf.getvalue()
        if r.value is not None:
            output += f"\n[Return value]: {_to_display_str(r.value)}"
        return {
            "success": True,
            "output": output,
            "error": None,
            "execution_time_ms": elapsed_ms,
        }
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "output": stdout_buf.getvalue(),
            "error": {
                "phase": "System",
                "message": f"Internal Error: {e}",
                "line": 0,
                "col": 0,
            },
            "execution_time_ms": elapsed_ms,
        }
    finally:
        sys.stdout = old_stdout


def get_tokens(source: str, filename: str = "<web>") -> dict[str, Any]:
    """Tokenize Akasha source code and return detailed token objects."""
    try:
        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()
        token_list = [
            {
                "kind": t.kind.name,
                "value": t.value,
                "line": t.line,
                "col": t.col,
            }
            for t in tokens
        ]
        return {"success": True, "tokens": token_list, "count": len(token_list)}
    except LexerError as e:
        return {"success": False, "error": str(e), "line": getattr(e, "line", 0), "col": getattr(e, "col", 0)}


def get_ast(source: str, filename: str = "<web>") -> dict[str, Any]:
    """Parse Akasha source code and return AST structure."""
    try:
        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        ast_dict = ast_to_dict(program)
        return {"success": True, "ast": ast_dict}
    except (LexerError, ParseError) as e:
        return {"success": False, "error": str(e)}


# ── HTTP Request Handler ──────────────────────────────────────────────────────

class AkashaWebHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler serving the web compiler API and static assets."""

    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_headers(200)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/examples":
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"examples": EXAMPLES}, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/health":
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "ok", "version": "0.1.0"}).encode("utf-8"))
            return

        # Serve static assets
        if path == "/" or path == "/index.html":
            file_path = STATIC_DIR / "index.html"
            content_type = "text/html; charset=utf-8"
        elif path.endswith(".css"):
            file_path = STATIC_DIR / path.lstrip("/")
            content_type = "text/css; charset=utf-8"
        elif path.endswith(".js"):
            file_path = STATIC_DIR / path.lstrip("/")
            content_type = "application/javascript; charset=utf-8"
        elif path.endswith(".svg"):
            file_path = STATIC_DIR / path.lstrip("/")
            content_type = "image/svg+xml"
        elif path.endswith(".json"):
            file_path = STATIC_DIR / path.lstrip("/")
            content_type = "application/json"
        else:
            file_path = STATIC_DIR / path.lstrip("/")
            content_type = "application/octet-stream"

        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_bytes()
                self._set_headers(200, content_type)
                self.wfile.write(content)
            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(f"Error reading static file: {e}".encode("utf-8"))
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"404 Not Found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            body = json.loads(post_data)
        except json.JSONDecodeError:
            self._set_headers(400, "application/json")
            self.wfile.write(json.dumps({"success": False, "error": "Invalid JSON body"}).encode("utf-8"))
            return

        source = body.get("code", "")

        if path == "/api/run":
            result = run_code(source)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/check":
            try:
                tokens = Lexer(source).tokenize()
                Parser(tokens).parse()
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps({"success": True, "message": "Syntax is valid!"}).encode("utf-8"))
            except Exception as e:
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        if path == "/api/tokens":
            result = get_tokens(source)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/ast":
            result = get_ast(source)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        # Clean logging format
        if os.environ.get("AKASHA_WEB_LOG"):
            sys.stderr.write(f"[Akasha Web] {self.address_string()} - {format % args}\n")


def start_server(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = False) -> None:
    """Start the Akasha Web Compiler server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, AkashaWebHandler)
    url = f"http://{host}:{port}"
    print(f"""
  ======================================================
     Akasha Programming Language — Web Playground
  ======================================================
  * Running on: {url}
  * Press Ctrl+C to stop the server
""")
    if open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Akasha Web Compiler...")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start Akasha Web Compiler & Playground")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port number (default: 8080)")
    parser.add_argument("--open", "-o", action="store_true", help="Open in default web browser")
    args = parser.parse_args()
    start_server(args.host, args.port, args.open)
