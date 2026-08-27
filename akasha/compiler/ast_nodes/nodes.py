"""
Akasha Programming Language — AST Node Definitions
=================================================

Every syntactic construct in a Akasha program is represented as an AST node.
All nodes are Python dataclasses, making them:
  - Immutable (frozen)
  - Printable (repr)
  - Comparable (eq)

Node hierarchy:
  Node (base)
    ├── Statement nodes  (do something)
    └── Expression nodes (produce a value)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


# ── Base ─────────────────────────────────────────────────────────────────────

@dataclass
class Node:
    """Base class for all AST nodes. Carries source location."""
    line: int = field(default=0, compare=False, kw_only=True)
    col:  int = field(default=0, compare=False, kw_only=True)



# ── Program Root ─────────────────────────────────────────────────────────────

@dataclass
class Program(Node):
    """The root node — a list of top-level statements."""
    body: list[Node]


# ══════════════════════════════════════════════════════════════════════════════
# EXPRESSIONS  (produce a value)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class IntLiteral(Node):
    """42, 0xFF, 1_000"""
    value: int

@dataclass
class FloatLiteral(Node):
    """3.14, 2.0e5"""
    value: float

@dataclass
class StringLiteral(Node):
    """\"hello\" or 'world'"""
    value: str

@dataclass
class FStringLiteral(Node):
    """f\"Hello, {name}!\"
    Parts is a list of either str (literal text) or Node (expression).
    """
    parts: list[str | Node]

@dataclass
class BoolLiteral(Node):
    """nijam (true) or abaddham (false)"""
    value: bool

@dataclass
class NullLiteral(Node):
    """shunyam"""
    pass

@dataclass
class Identifier(Node):
    """A reference to a variable or function name."""
    name: str

@dataclass
class BinaryOp(Node):
    """left op right  e.g.  a + b,  x >= 10"""
    left:     Node
    operator: str
    right:    Node

@dataclass
class UnaryOp(Node):
    """!expr  or  -expr"""
    operator: str
    operand:  Node

@dataclass
class Assignment(Node):
    """name = expr"""
    name:  str
    value: Node

@dataclass
class Call(Node):
    """callee(arg1, arg2, ...)"""
    callee:    Node        # could be Identifier or field access
    arguments: list[Node]

@dataclass
class Index(Node):
    """collection[index]"""
    obj:   Node
    index: Node

@dataclass
class Slice(Node):
    """collection[start..end]"""
    obj:   Node
    start: Node
    end:   Node

@dataclass
class IndexAssignment(Node):
    """obj[index] = value"""
    obj:   Node
    index: Node
    value: Node


@dataclass
class FieldAccess(Node):
    """obj.field"""
    obj:   Node
    field: str

@dataclass
class ArrayLiteral(Node):
    """[expr, expr, ...]"""
    elements: list[Node]

@dataclass
class MapLiteral(Node):
    """{ "key": value, ... }"""
    pairs: list[tuple[Node, Node]]

@dataclass
class TupleLiteral(Node):
    """(a, b, c)"""
    elements: list[Node]

@dataclass
class RangeExpr(Node):
    """start..end"""
    start: Node
    end:   Node

@dataclass
class Closure(Node):
    """muppu(params) => expr_or_block"""
    params: list[Param]
    body:   Node          # either a Block or a single expression

@dataclass
class MethodCall(Node):
    """obj.method(args)"""
    obj:    Node
    method: str
    args:   list[Node]


# ══════════════════════════════════════════════════════════════════════════════
# TYPE ANNOTATIONS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TypeAnnotation(Node):
    """A type name, e.g. Sankhya, Padam, Patrika[Sankhya]"""
    name:       str
    params:     list[TypeAnnotation] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# STATEMENTS  (do something)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Block(Node):
    """A { ... } block containing a sequence of statements."""
    body: list[Node]

@dataclass
class ExprStatement(Node):
    """A standalone expression used as a statement (e.g., function call)."""
    expr: Node

@dataclass
class VarDecl(Node):
    """viluva name [: type] = value"""
    name:    str
    type_:   Optional[TypeAnnotation]
    value:   Node
    mutable: bool = True     # viluva → mutable, sthiram → immutable

@dataclass
class ConstDecl(Node):
    """sthiram NAME [: type] = value"""
    name:  str
    type_: Optional[TypeAnnotation]
    value: Node

@dataclass
class SecretDecl(Node):
    """rahasyam name = expr"""
    name:  str
    value: Node

@dataclass
class Param(Node):
    """A function parameter: name [: type] [= default]"""
    name:    str
    type_:   Optional[TypeAnnotation]
    default: Optional[Node]

@dataclass
class FunctionDecl(Node):
    """karyam name(params) [: return_type] { body }"""
    name:        str
    params:      list[Param]
    return_type: Optional[TypeAnnotation]
    body:        Block
    is_async:    bool = False

@dataclass
class ReturnStmt(Node):
    """phalitham [expr]"""
    value: Optional[Node]

@dataclass
class IfStmt(Node):
    """okavela cond { ... } [mariyu cond { ... }]* [lekapothe { ... }]"""
    condition:   Node
    then_block:  Block
    elif_arms:   list[tuple[Node, Block]]   # list of (condition, block)
    else_block:  Optional[Block]

@dataclass
class WhileStmt(Node):
    """alaa condition { body }"""
    condition: Node
    body:      Block

@dataclass
class ForEachStmt(Node):
    """prathi var lo iterable { body }"""
    var:      str
    iterable: Node
    body:     Block

@dataclass
class LoopStmt(Node):
    """loop { body }  — infinite loop"""
    body: Block

@dataclass
class BreakStmt(Node):
    """aapu"""
    pass

@dataclass
class ContinueStmt(Node):
    """konasaginchu"""
    pass

@dataclass
class MatchArm(Node):
    """sthithi pattern => expr_or_block"""
    pattern:  Node           # a literal, wildcard, or enum pattern
    body:     Node           # expression or Block

@dataclass
class MatchStmt(Node):
    """tirugu expr { arms... [default => ...] }"""
    subject: Node
    arms:    list[MatchArm]
    default: Optional[Node]  # the default arm body (if any)

@dataclass
class ImportStmt(Node):
    """digumathi module [vethuku name]"""
    module: str
    name:   Optional[str]    # specific import, or None for whole module

@dataclass
class ExportStmt(Node):
    """egumathi decl"""
    decl: Node

@dataclass
class StructDecl(Node):
    """rachana Name { fields... }"""
    name:   str
    fields: list[tuple[str, TypeAnnotation]]

@dataclass
class StructLiteral(Node):
    """TypeName { field: value, ... }"""
    name:   str
    fields: list[tuple[str, Node]]

@dataclass
class EnumDecl(Node):
    """vishayam Name { Variant, ... }"""
    name:     str
    variants: list[tuple[str, Optional[list[TypeAnnotation]]]]

@dataclass
class TraitDecl(Node):
    """nerpu Name { method signatures... }"""
    name:    str
    methods: list[FunctionDecl]

@dataclass
class ImplBlock(Node):
    """adugu Type nerpu Trait { methods... }"""
    type_name:  str
    trait_name: Optional[str]
    methods:    list[FunctionDecl]

@dataclass
class UnsafeBlock(Node):
    """asura { body }"""
    body: Block

@dataclass
class PropagateError(Node):
    """expr?  — propagate error upward"""
    expr: Node
