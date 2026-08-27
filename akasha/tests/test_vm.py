"""
Akasha Stack-Based VM Unit & Integration Tests
==============================================

Tests VM execution of compiled bytecode and .akb serialization.
"""

import sys
import io
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.compiler.lexer.lexer import Lexer
from akasha.compiler.parser.parser import Parser
from akasha.compiler.bytecode.compiler import BytecodeCompiler
from akasha.compiler.bytecode.serializer import (
    serialize_to_bytes, deserialize_from_bytes, save_bytecode_file, load_bytecode_file
)
from akasha.runtime.vm import AkashaVM


def run_vm(source: str) -> str:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    chunk = BytecodeCompiler("<test>").compile(ast)
    buf = io.StringIO()
    vm = AkashaVM(stdout=buf)
    vm.execute(chunk)
    return buf.getvalue()


class TestVMExecution:
    def test_hello_world(self):
        output = run_vm('cheppu("Namaste from Akasha VM!")')
        assert "Namaste from Akasha VM!" in output

    def test_arithmetic_operations(self):
        code = """
viluva a = 10
viluva b = 25
cheppu(a + b)
cheppu(b - a)
cheppu(a * 4)
cheppu(b / 5)
cheppu(b % 4)
cheppu(2 ** 8)
"""
        out = run_vm(code).strip().splitlines()
        assert out == ["35", "15", "40", "5.0", "1", "256"]

    def test_conditionals(self):
        code = """
viluva score = 85
okavela score >= 90 {
    cheppu("A+")
} mariyu score >= 80 {
    cheppu("A")
} lekapothe {
    cheppu("B")
}
"""
        assert "A\n" in run_vm(code)

    def test_while_loop(self):
        code = """
viluva i = 1
viluva sum = 0
alaa i <= 5 {
    sum = sum + i
    i = i + 1
}
cheppu(sum)
"""
        assert "15" in run_vm(code)

    def test_for_each_array(self):
        code = """
viluva items = ["a", "b", "c"]
prathi x lo items {
    cheppu(x)
}
"""
        out = run_vm(code).strip().splitlines()
        assert out == ["a", "b", "c"]

    def test_recursive_function(self):
        code = """
karyam fact(n) {
    okavela n <= 1 { phalitham 1 }
    phalitham n * fact(n - 1)
}
cheppu(fact(5))
"""
        assert "120" in run_vm(code)

    def test_fstring_formatting(self):
        code = """
viluva name = "Akasha"
viluva n = 42
cheppu(f"Language: {name}, Value: {n}")
"""
        assert "Language: Akasha, Value: 42" in run_vm(code)


class TestBinarySerialization:
    def test_akb_roundtrip(self):
        source = """
karyam square(x) {
    phalitham x * x
}
cheppu(square(9))
"""
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        chunk = BytecodeCompiler("math.akasha").compile(ast)

        # Serialize to bytes
        binary_data = serialize_to_bytes(chunk)
        assert binary_data.startswith(b"AKB\x01\x00")

        # Deserialize back
        restored_chunk = deserialize_from_bytes(binary_data)
        assert restored_chunk.name == "<module>"
        assert len(restored_chunk.instructions) == len(chunk.instructions)

        # Execute restored chunk in VM
        buf = io.StringIO()
        vm = AkashaVM(stdout=buf)
        vm.execute(restored_chunk)
        assert "81" in buf.getvalue()

    def test_akb_disk_file_io(self):
        source = 'cheppu("Loaded from .akb file!")'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        chunk = BytecodeCompiler("test.akasha").compile(ast)

        with tempfile.NamedTemporaryFile(suffix=".akb", delete=False) as tf:
            temp_path = tf.name

        try:
            save_bytecode_file(chunk, temp_path)
            loaded_chunk = load_bytecode_file(temp_path)
            buf = io.StringIO()
            AkashaVM(stdout=buf).execute(loaded_chunk)
            assert "Loaded from .akb file!" in buf.getvalue()
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
