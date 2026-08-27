"""
Akasha Programming Language — Runtime Values
============================================

Defines the Python objects that represent Akasha values at runtime.
Every Akasha value is one of these wrapper types.

Design goals:
- Clear distinction between Akasha types and Python types
- Support for Option (Vikalpa) and Result (Phalitham) types
- Callable objects for functions and closures
- Struct instance support
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ast_nodes.nodes import FunctionDecl, Closure, Block, Param


# ── Base ──────────────────────────────────────────────────────────────────────

class AkashaNullType:
    """Singleton representing shunyam (null)."""
    _instance: Optional["AkashaNullType"] = None

    def __new__(cls) -> "AkashaNullType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "shunyam"

    def __bool__(self) -> bool:
        return False


SHUNYAM = AkashaNullType()    # The one and only null value


# ── Akasha Runtime Types ──────────────────────────────────────────────────────

@dataclass
class AkashaInt:
    value: int

    def __repr__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AkashaInt):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class AkashaFloat:
    value: float

    def __repr__(self) -> str:
        s = f"{self.value}"
        return s

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AkashaFloat):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class AkashaBool:
    value: bool

    def __repr__(self) -> str:
        return "nijam" if self.value else "abaddham"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AkashaBool):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __bool__(self) -> bool:
        return self.value


@dataclass
class AkashaString:
    value: str

    def __repr__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AkashaString):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass
class AkashaArray:
    elements: list[Any]   # list of Akasha values

    def __repr__(self) -> str:
        items = ", ".join(repr(e) for e in self.elements)
        return f"[{items}]"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AkashaArray):
            return self.elements == other.elements
        return NotImplemented


@dataclass
class AkashaMap:
    pairs: dict[Any, Any]   # Akasha key → Akasha value

    def __repr__(self) -> str:
        items = ", ".join(f"{k!r}: {v!r}" for k, v in self.pairs.items())
        return "{" + items + "}"


@dataclass
class AkashaTuple:
    elements: list[Any]

    def __repr__(self) -> str:
        items = ", ".join(repr(e) for e in self.elements)
        return f"({items})"


# ── Option / Result ───────────────────────────────────────────────────────────

@dataclass
class AkashaOption:
    """Vikalpa[T] — Undu(value) | Ledu"""
    has_value: bool
    value: Any = None

    @classmethod
    def some(cls, v: Any) -> "AkashaOption":
        return cls(has_value=True, value=v)

    @classmethod
    def none(cls) -> "AkashaOption":
        return cls(has_value=False, value=None)

    def __repr__(self) -> str:
        if self.has_value:
            return f"Undu({self.value!r})"
        return "Ledu"


@dataclass
class AkashaResult:
    """Phalitham[T] — Sari(value) | Tappu(error)"""
    ok:    bool
    value: Any = None     # set when ok=True
    error: Any = None     # set when ok=False

    @classmethod
    def sari(cls, v: Any) -> "AkashaResult":
        return cls(ok=True, value=v)

    @classmethod
    def tappu(cls, e: Any) -> "AkashaResult":
        return cls(ok=False, error=e)

    def __repr__(self) -> str:
        if self.ok:
            return f"Sari({self.value!r})"
        return f"Tappu({self.error!r})"


# ── Callables ─────────────────────────────────────────────────────────────────

@dataclass
class AkashaFunction:
    """A user-defined function (karyam)."""
    name:    str
    params:  list[Any]         # list of Param AST nodes
    body:    Any               # Block AST node
    closure: "Environment"     # captured environment (lexical scope)
    is_async: bool = False

    def __repr__(self) -> str:
        return f"<karyam {self.name}>"

    def __call__(self, *args: Any) -> Any:
        raise NotImplementedError("Use interpreter.call_function()")


@dataclass
class AkashaClosure:
    """An anonymous function (muppu)."""
    params:  list[Any]         # Param nodes
    body:    Any               # Block or expression node
    closure: "Environment"

    def __repr__(self) -> str:
        return "<muppu>"


@dataclass
class AkashaBuiltin:
    """A built-in function implemented in Python."""
    name: str
    fn:   Any    # callable

    def __repr__(self) -> str:
        return f"<builtin {self.name}>"


# ── Struct Instance ───────────────────────────────────────────────────────────

@dataclass
class AkashaStruct:
    """An instance of a user-defined rachana (struct)."""
    type_name: str
    fields:    dict[str, Any]   # field name → Akasha value

    def __repr__(self) -> str:
        items = ", ".join(f"{k}: {v!r}" for k, v in self.fields.items())
        return f"{self.type_name} {{ {items} }}"


# ── Environment (Symbol Table / Scope) ───────────────────────────────────────

class Environment:
    """
    A lexical scope: maps names to Akasha runtime values.

    Scopes are chained: inner scope → outer scope → ... → global scope.
    Variable lookup walks outward until found or raises NameError.
    """

    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self._parent   = parent
        self._bindings: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        """Create a new binding in the current scope."""
        self._bindings[name] = value

    def assign(self, name: str, value: Any) -> None:
        """Assign to an existing variable (walks scopes outward)."""
        if name in self._bindings:
            self._bindings[name] = value
        elif self._parent is not None:
            self._parent.assign(name, value)
        else:
            raise AkashaRuntimeError(
                f"Variable '{name}' is not defined.\n"
                f"  Hint: Use 'viluva {name} = ...' to declare it first."
            )

    def get(self, name: str) -> Any:
        """Look up a variable (walks scopes outward)."""
        if name in self._bindings:
            return self._bindings[name]
        if self._parent is not None:
            return self._parent.get(name)
        raise AkashaRuntimeError(
            f"Variable '{name}' was not found.",
            suggestion=f"viluva {name} = ..."
        )

    def has(self, name: str) -> bool:
        if name in self._bindings:
            return True
        if self._parent:
            return self._parent.has(name)
        return False

    def child(self) -> "Environment":
        """Create a new child scope."""
        return Environment(parent=self)


# ── Control Flow Signals ──────────────────────────────────────────────────────

class ReturnSignal(Exception):
    """Raised when 'phalitham' (return) is executed."""
    def __init__(self, value: Any) -> None:
        self.value = value


class BreakSignal(Exception):
    """Raised when 'aapu' (break) is executed."""
    pass


class ContinueSignal(Exception):
    """Raised when 'konasaginchu' (continue) is executed."""
    pass


# ── Runtime Error ─────────────────────────────────────────────────────────────

class AkashaRuntimeError(Exception):
    """Raised when a runtime error occurs during interpretation."""

    def __init__(self, message: str, line: int = 0, col: int = 0,
                 suggestion: str = "") -> None:
        self.line       = line
        self.col        = col
        self.suggestion = suggestion
        loc  = f" at line {line}, col {col}" if line else ""
        hint = f"\n  Hint: {suggestion}" if suggestion else ""
        super().__init__(f"\nRuntime Error{loc}:\n  {message}{hint}\n")


# ── Shared Display Helper ─────────────────────────────────────────────────────

def _to_display_str(val: Any) -> str:
    """Convert an Akasha value to its human-readable display string."""
    if isinstance(val, AkashaString):
        return val.value
    if isinstance(val, AkashaBool):
        return "nijam" if val.value else "abaddham"
    if isinstance(val, AkashaNullType):
        return "shunyam"
    if isinstance(val, AkashaInt):
        return str(val.value)
    if isinstance(val, AkashaFloat):
        f = val.value
        if f == int(f) and abs(f) < 1e15:
            return f"{f:.1f}"
        return str(f)
    if isinstance(val, AkashaArray):
        items = ", ".join(_to_display_str(e) for e in val.elements)
        return f"[{items}]"
    if isinstance(val, AkashaMap):
        items = ", ".join(
            f"{_to_display_str(k)}: {_to_display_str(v)}"
            for k, v in val.pairs.items()
        )
        return "{" + items + "}"
    if isinstance(val, AkashaTuple):
        items = ", ".join(_to_display_str(e) for e in val.elements)
        return f"({items})"
    if isinstance(val, AkashaStruct):
        items = ", ".join(f"{k}: {_to_display_str(v)}" for k, v in val.fields.items())
        return f"{val.type_name} {{ {items} }}"
    if isinstance(val, AkashaOption):
        if val.has_value:
            return f"Undu({_to_display_str(val.value)})"
        return "Ledu"
    if isinstance(val, AkashaResult):
        if val.ok:
            return f"Sari({_to_display_str(val.value)})"
        return f"Tappu({_to_display_str(val.error)})"
    if isinstance(val, AkashaBuiltin):
        return f"<builtin {val.name}>"
    if isinstance(val, AkashaFunction):
        return f"<karyam {val.name}>"
    if isinstance(val, AkashaClosure):
        return "<muppu>"
    return str(val)


# ── Backward Compatibility Aliases ───────────────────────────────────────────
AkashaNullType = AkashaNullType
AkashaInt = AkashaInt
AkashaFloat = AkashaFloat
AkashaBool = AkashaBool
AkashaString = AkashaString
AkashaArray = AkashaArray
AkashaMap = AkashaMap
AkashaTuple = AkashaTuple
AkashaOption = AkashaOption
AkashaResult = AkashaResult
AkashaFunction = AkashaFunction
AkashaClosure = AkashaClosure
AkashaBuiltin = AkashaBuiltin
AkashaStruct = AkashaStruct
AkashaRuntimeError = AkashaRuntimeError
