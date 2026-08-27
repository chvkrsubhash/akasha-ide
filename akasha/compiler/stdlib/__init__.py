"""
Akasha Standard Library
=====================

v0.1 provides core built-in modules:
- math    : mathematical functions and constants
- io      : file and standard I/O
- string  : string utilities
- os      : OS-level utilities
- time    : time functions
"""

from __future__ import annotations
from typing import Any, Optional
import math as _math
import os as _os
import time as _time

from ..interpreter.values import (
    AkashaBuiltin, AkashaInt, AkashaFloat, AkashaString, AkashaArray,
    AkashaBool, SHUNYAM, AkashaRuntimeError,
)

def _ds(v: Any) -> str:
    """Convert Akasha value to display string (local helper)."""
    if isinstance(v, AkashaString):  return v.value
    if isinstance(v, AkashaInt):     return str(v.value)
    if isinstance(v, AkashaFloat):   return str(v.value)
    if isinstance(v, AkashaBool):    return "nijam" if v.value else "abaddham"
    from ..interpreter.values import AkashaNullType
    if isinstance(v, AkashaNullType): return "shunyam"
    return str(v)


# ── Math Module ───────────────────────────────────────────────────────────────

def _math_sqrt(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.sqrt() requires one argument")
    v = args[0]
    n = v.value if isinstance(v, (AkashaInt, AkashaFloat)) else float(str(v))
    return AkashaFloat(_math.sqrt(n))

def _math_abs(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.abs() requires one argument")
    v = args[0]
    if isinstance(v, AkashaInt):   return AkashaInt(abs(v.value))
    if isinstance(v, AkashaFloat): return AkashaFloat(abs(v.value))
    raise AkashaRuntimeError("math.abs() requires a number")

def _math_pow(args: list[Any]) -> Any:
    if len(args) < 2: raise AkashaRuntimeError("math.pow() requires 2 arguments")
    base = args[0].value if isinstance(args[0], (AkashaInt, AkashaFloat)) else 0
    exp  = args[1].value if isinstance(args[1], (AkashaInt, AkashaFloat)) else 0
    result = _math.pow(base, exp)
    return AkashaFloat(result)

def _math_floor(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.floor() requires one argument")
    v = args[0]
    n = v.value if isinstance(v, (AkashaInt, AkashaFloat)) else 0
    return AkashaInt(_math.floor(n))

def _math_ceil(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.ceil() requires one argument")
    v = args[0]
    n = v.value if isinstance(v, (AkashaInt, AkashaFloat)) else 0
    return AkashaInt(_math.ceil(n))

def _math_round(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.round() requires one argument")
    v = args[0]
    n = v.value if isinstance(v, (AkashaInt, AkashaFloat)) else 0
    return AkashaInt(round(n))

def _math_log(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.log() requires one argument")
    v = args[0]
    n = v.value if isinstance(v, (AkashaInt, AkashaFloat)) else 0
    return AkashaFloat(_math.log(n))

def _math_log10(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.log10() requires one argument")
    v = args[0]
    n = v.value if isinstance(v, (AkashaInt, AkashaFloat)) else 0
    return AkashaFloat(_math.log10(n))

def _math_sin(args: list[Any]) -> Any:
    v = args[0].value if args and isinstance(args[0], (AkashaInt, AkashaFloat)) else 0
    return AkashaFloat(_math.sin(v))

def _math_cos(args: list[Any]) -> Any:
    v = args[0].value if args and isinstance(args[0], (AkashaInt, AkashaFloat)) else 0
    return AkashaFloat(_math.cos(v))

def _math_tan(args: list[Any]) -> Any:
    v = args[0].value if args and isinstance(args[0], (AkashaInt, AkashaFloat)) else 0
    return AkashaFloat(_math.tan(v))

def _math_max(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.max() requires arguments")
    vals = [a.value for a in args if isinstance(a, (AkashaInt, AkashaFloat))]
    result = max(vals)
    return AkashaInt(int(result)) if isinstance(result, int) else AkashaFloat(result)

def _math_min(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("math.min() requires arguments")
    vals = [a.value for a in args if isinstance(a, (AkashaInt, AkashaFloat))]
    result = min(vals)
    return AkashaInt(int(result)) if isinstance(result, int) else AkashaFloat(result)

MATH_MODULE: dict[str, Any] = {
    "sqrt":  AkashaBuiltin("sqrt",  _math_sqrt),
    "abs":   AkashaBuiltin("abs",   _math_abs),
    "pow":   AkashaBuiltin("pow",   _math_pow),
    "floor": AkashaBuiltin("floor", _math_floor),
    "ceil":  AkashaBuiltin("ceil",  _math_ceil),
    "round": AkashaBuiltin("round", _math_round),
    "log":   AkashaBuiltin("log",   _math_log),
    "log10": AkashaBuiltin("log10", _math_log10),
    "sin":   AkashaBuiltin("sin",   _math_sin),
    "cos":   AkashaBuiltin("cos",   _math_cos),
    "tan":   AkashaBuiltin("tan",   _math_tan),
    "max":   AkashaBuiltin("max",   _math_max),
    "min":   AkashaBuiltin("min",   _math_min),
    "PI":    AkashaFloat(_math.pi),
    "E":     AkashaFloat(_math.e),
    "TAU":   AkashaFloat(_math.tau),
    "INF":   AkashaFloat(float("inf")),
}


# ── IO Module ─────────────────────────────────────────────────────────────────

def _io_read(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("io.read() requires a file path")
    path = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
    try:
        with open(path, "r", encoding="utf-8") as f:
            return AkashaString(f.read())
    except FileNotFoundError:
        raise AkashaRuntimeError(f"File not found: '{path}'")
    except Exception as e:
        raise AkashaRuntimeError(f"IO error reading '{path}': {e}")

def _io_write(args: list[Any]) -> Any:
    if len(args) < 2: raise AkashaRuntimeError("io.write() requires path and content")
    path    = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
    content = _ds(args[1])
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return SHUNYAM
    except Exception as e:
        raise AkashaRuntimeError(f"IO error writing '{path}': {e}")

def _io_append(args: list[Any]) -> Any:
    if len(args) < 2: raise AkashaRuntimeError("io.append() requires path and content")
    path    = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
    content = _ds(args[1])
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return SHUNYAM
    except Exception as e:
        raise AkashaRuntimeError(f"IO error appending '{path}': {e}")

def _io_exists(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("io.exists() requires a path")
    path = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
    return AkashaBool(_os.path.exists(path))

IO_MODULE: dict[str, Any] = {
    "read":   AkashaBuiltin("read",   _io_read),
    "write":  AkashaBuiltin("write",  _io_write),
    "append": AkashaBuiltin("append", _io_append),
    "exists": AkashaBuiltin("exists", _io_exists),
}


# ── String Module ─────────────────────────────────────────────────────────────

def _str_format(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("string.format() requires arguments")
    template = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
    rest = [_ds(a) for a in args[1:]]
    try:
        return AkashaString(template.format(*rest))
    except Exception as e:
        raise AkashaRuntimeError(f"string.format() error: {e}")

def _str_repeat(args: list[Any]) -> Any:
    if len(args) < 2: raise AkashaRuntimeError("string.repeat() requires 2 arguments")
    s = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
    n = args[1].value if isinstance(args[1], AkashaInt) else int(str(args[1]))
    return AkashaString(s * n)

STRING_MODULE: dict[str, Any] = {
    "format": AkashaBuiltin("format", _str_format),
    "repeat": AkashaBuiltin("repeat", _str_repeat),
}


# ── OS Module ─────────────────────────────────────────────────────────────────

def _os_env(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("os.env() requires a key")
    key = args[0].value if isinstance(args[0], AkashaString) else str(args[0])
    val = _os.environ.get(key)
    return AkashaString(val) if val else SHUNYAM

def _os_cwd(args: list[Any]) -> Any:
    return AkashaString(_os.getcwd())

def _os_args(args: list[Any]) -> Any:
    import sys
    return AkashaArray([AkashaString(a) for a in sys.argv[1:]])

OS_MODULE: dict[str, Any] = {
    "env":  AkashaBuiltin("env",  _os_env),
    "cwd":  AkashaBuiltin("cwd",  _os_cwd),
    "args": AkashaBuiltin("args", _os_args),
}


# ── Time Module ───────────────────────────────────────────────────────────────

def _time_now(args: list[Any]) -> Any:
    return AkashaFloat(_time.time())

def _time_sleep(args: list[Any]) -> Any:
    if not args: raise AkashaRuntimeError("time.sleep() requires seconds argument")
    secs = args[0].value if isinstance(args[0], (AkashaInt, AkashaFloat)) else 1
    _time.sleep(secs)
    return SHUNYAM

TIME_MODULE: dict[str, Any] = {
    "now":   AkashaBuiltin("now",   _time_now),
    "sleep": AkashaBuiltin("sleep", _time_sleep),
}


# ── Module Registry ───────────────────────────────────────────────────────────

_MODULES: dict[str, dict[str, Any]] = {
    "math":   MATH_MODULE,
    "io":     IO_MODULE,
    "string": STRING_MODULE,
    "os":     OS_MODULE,
    "time":   TIME_MODULE,
}


def get_module(name: str) -> Optional[dict[str, Any]]:
    """Return the module dict for the given name, or None if not found."""
    return _MODULES.get(name)


def available_modules() -> list[str]:
    return list(_MODULES.keys())
