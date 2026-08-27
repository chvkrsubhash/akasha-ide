"""
Akasha Bytecode Compiler Unit Tests
====================================

Tests compilation of Akasha AST into stack-based VM instructions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.compiler.lexer.lexer import Lexer
from akasha.compiler.parser.parser import Parser
from akasha.compiler.bytecode.compiler import BytecodeCompiler
from akasha.compiler.bytecode.opcodes import OpCode
from akasha.compiler.bytecode.serializer import disassemble


def compile_src(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    compiler = BytecodeCompiler("<test>")
    return compiler.compile(ast)


class TestBytecodeCompiler:
    def test_compile_arithmetic(self):
        chunk = compile_src("viluva x = 10 + 20")
        opcodes = [inst.opcode for inst in chunk.instructions]
        assert OpCode.LOAD_CONST in opcodes
        assert OpCode.BINARY_ADD in opcodes
        assert OpCode.STORE_NAME in opcodes

    def test_compile_if_statement_jump_patching(self):
        chunk = compile_src("""
okavela x > 10 {
    cheppu("big")
} lekapothe {
    cheppu("small")
}
""")
        opcodes = [inst.opcode for inst in chunk.instructions]
        assert OpCode.POP_JUMP_IF_FALSE in opcodes
        assert OpCode.JUMP_ABSOLUTE in opcodes
        # Verify jump target is valid instruction index
        for inst in chunk.instructions:
            if inst.opcode in (OpCode.POP_JUMP_IF_FALSE, OpCode.JUMP_ABSOLUTE):
                assert 0 <= inst.arg < len(chunk.instructions)

    def test_compile_while_loop(self):
        chunk = compile_src("""
viluva i = 0
alaa i < 5 {
    i = i + 1
}
""")
        opcodes = [inst.opcode for inst in chunk.instructions]
        assert OpCode.POP_JUMP_IF_FALSE in opcodes
        assert OpCode.JUMP_ABSOLUTE in opcodes

    def test_compile_for_each(self):
        chunk = compile_src("""
prathi n lo [1, 2, 3] {
    cheppu(n)
}
""")
        opcodes = [inst.opcode for inst in chunk.instructions]
        assert OpCode.GET_ITER in opcodes
        assert OpCode.FOR_ITER in opcodes
        assert OpCode.PRINT_EXPR in opcodes

    def test_compile_function_decl(self):
        chunk = compile_src("""
karyam add(a, b) {
    phalitham a + b
}
viluva res = add(5, 7)
""")
        opcodes = [inst.opcode for inst in chunk.instructions]
        assert OpCode.MAKE_FUNCTION in opcodes
        assert OpCode.CALL_FUNCTION in opcodes

    def test_disassembly_not_empty(self):
        chunk = compile_src("cheppu('Hello')")
        dis_text = disassemble(chunk)
        assert "PRINT_EXPR" in dis_text
        assert "LOAD_CONST" in dis_text
