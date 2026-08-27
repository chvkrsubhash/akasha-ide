"""
Akasha Programming Language — Token Definitions
=============================================

Every piece of source code the lexer reads becomes a Token.
Each Token carries:
  - kind   : TokenKind enum value
  - value  : the raw text from source
  - line   : 1-based line number
  - col    : 1-based column number
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass


class TokenKind(Enum):
    # ── Literals ─────────────────────────────────────────────────────────────
    INTEGER     = auto()   # 42, 0xFF, 1_000
    FLOAT       = auto()   # 3.14
    STRING      = auto()   # "hello" or 'hello'
    FSTRING     = auto()   # f"Hello, {name}!" (raw text, interpolation resolved in parser)
    BOOL_TRUE   = auto()   # nijam
    BOOL_FALSE  = auto()   # abaddham
    NULL        = auto()   # shunyam

    # ── Identifiers & Keywords ───────────────────────────────────────────────
    IDENT       = auto()   # user-defined names

    # Control flow
    OKAVELA     = auto()   # if
    LEKAPOTHE   = auto()   # else
    MARIYU      = auto()   # else-if
    ALAA        = auto()   # while
    PRATHI      = auto()   # for-each
    LOOP        = auto()   # infinite loop
    AAPU        = auto()   # break
    KONASAGINCHU= auto()   # continue
    TIRUGU      = auto()   # match
    STHITHI     = auto()   # case
    DEFAULT     = auto()   # default

    # Functions
    KARYAM      = auto()   # function
    PHALITHAM   = auto()   # return
    MUPPU       = auto()   # closure/lambda
    ASYNCHRONOUS= auto()   # async
    NEKKADI     = auto()   # await

    # Variables / bindings
    VILUVA      = auto()   # let / var
    STHIRAM     = auto()   # const
    RAHASYAM    = auto()   # secret
    MAARPU      = auto()   # mut (mutable modifier)

    # Types
    SANKHYA     = auto()   # Int
    DASAMSAM    = auto()   # Float
    PADAM       = auto()   # String
    NIJAM_TYPE  = auto()   # Bool
    SHUNYAM_TYPE= auto()   # Null type
    BYTE        = auto()   # Byte
    PATRIKA     = auto()   # Array
    NAKSHA      = auto()   # Map
    GUMPU       = auto()   # Set
    JANTA       = auto()   # Tuple
    VIKALPA     = auto()   # Option
    PHAL_TYPE   = auto()   # Result (Phalitham as type)

    # Structures / OOP
    RACHANA     = auto()   # struct
    NERPU       = auto()   # trait
    ADUGU       = auto()   # impl
    VISHAYAM    = auto()   # enum
    TARAMA      = auto()   # type alias
    SELF        = auto()   # self

    # Modules
    DIGUMATHI   = auto()   # import
    EGUMATHI    = auto()   # export
    MODULU      = auto()   # module
    VETHUKU     = auto()   # from

    # Memory / Safety
    ASURA       = auto()   # unsafe
    DARUVU      = auto()   # borrow ref
    SWANTHAM    = auto()   # owned
    MUKKU       = auto()   # raw pointer

    # Error handling
    PRAYATHNINCHU = auto() # try
    PATTUKO     = auto()   # catch
    VIDUDALA    = auto()   # finally
    TAPPU       = auto()   # error/throw
    TAPPUDU     = auto()   # ok/no-error

    # Concurrency
    SAMAANAKAALAM = auto() # parallel
    VELLU       = auto()   # spawn
    KAANAL      = auto()   # channel
    NADUMU      = auto()   # mutex

    # Boolean values (as keywords, not types)
    # (handled via BOOL_TRUE / BOOL_FALSE above)

    # Range keyword
    LO          = auto()   # in  (prathi x lo ...)
    KI          = auto()   # to  (range to)

    # ── Operators ────────────────────────────────────────────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    PERCENT     = auto()   # %
    STAR_STAR   = auto()   # **  (power)
    EQ          = auto()   # =
    EQ_EQ       = auto()   # ==
    BANG_EQ     = auto()   # !=
    LT          = auto()   # <
    LT_EQ       = auto()   # <=
    GT          = auto()   # >
    GT_EQ       = auto()   # >=
    AND_AND     = auto()   # &&
    OR_OR       = auto()   # ||
    BANG        = auto()   # !
    QUESTION    = auto()   # ?   (error propagation)
    ARROW       = auto()   # =>  (match arm / closure)
    THIN_ARROW  = auto()   # ->  (return type)
    DOT         = auto()   # .
    DOT_DOT     = auto()   # ..  (range)
    AMP         = auto()   # &   (borrow)

    # ── Delimiters ───────────────────────────────────────────────────────────
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    LBRACKET    = auto()   # [
    RBRACKET    = auto()   # ]
    COMMA       = auto()   # ,
    COLON       = auto()   # :
    SEMICOLON   = auto()   # ;
    NEWLINE     = auto()   # \n (significant in some contexts)

    # ── Special ──────────────────────────────────────────────────────────────
    EOF         = auto()
    COMMENT     = auto()   # -- ...  (skipped)


# Maps keyword strings to TokenKind
KEYWORDS: dict[str, TokenKind] = {
    # Control flow
    "okavela":       TokenKind.OKAVELA,
    "lekapothe":     TokenKind.LEKAPOTHE,
    "mariyu":        TokenKind.MARIYU,
    "alaa":          TokenKind.ALAA,
    "prathi":        TokenKind.PRATHI,
    "loop":          TokenKind.LOOP,
    "aapu":          TokenKind.AAPU,
    "konasaginchu":  TokenKind.KONASAGINCHU,
    "tirugu":        TokenKind.TIRUGU,
    "sthithi":       TokenKind.STHITHI,
    "default":       TokenKind.DEFAULT,

    # Functions
    "karyam":        TokenKind.KARYAM,
    "phalitham":     TokenKind.PHALITHAM,
    "muppu":         TokenKind.MUPPU,
    "asynchronous":  TokenKind.ASYNCHRONOUS,
    "nekkadi":       TokenKind.NEKKADI,

    # Variables
    "viluva":        TokenKind.VILUVA,
    "sthiram":       TokenKind.STHIRAM,
    "rahasyam":      TokenKind.RAHASYAM,
    "maarpu":        TokenKind.MAARPU,

    # Types
    "Sankhya":       TokenKind.SANKHYA,
    "Dasamsam":      TokenKind.DASAMSAM,
    "Padam":         TokenKind.PADAM,
    "Nijam":         TokenKind.NIJAM_TYPE,
    "Byte":          TokenKind.BYTE,
    "Patrika":       TokenKind.PATRIKA,
    "Naksha":        TokenKind.NAKSHA,
    "Gumpu":         TokenKind.GUMPU,
    "Janta":         TokenKind.JANTA,
    "Vikalpa":       TokenKind.VIKALPA,

    # Boolean / null literals
    "nijam":         TokenKind.BOOL_TRUE,
    "abaddham":      TokenKind.BOOL_FALSE,
    "shunyam":       TokenKind.NULL,

    # Structures / OOP
    "rachana":       TokenKind.RACHANA,
    "nerpu":         TokenKind.NERPU,
    "adugu":         TokenKind.ADUGU,
    "vishayam":      TokenKind.VISHAYAM,
    "tarama":        TokenKind.TARAMA,
    "self":          TokenKind.SELF,

    # Modules
    "digumathi":     TokenKind.DIGUMATHI,
    "egumathi":      TokenKind.EGUMATHI,
    "modulu":        TokenKind.MODULU,
    "vethuku":       TokenKind.VETHUKU,

    # Memory / Safety
    "asura":         TokenKind.ASURA,
    "daruvu":        TokenKind.DARUVU,
    "swantham":      TokenKind.SWANTHAM,
    "mukku":         TokenKind.MUKKU,

    # Error handling
    "prayathninchu": TokenKind.PRAYATHNINCHU,
    "pattuko":       TokenKind.PATTUKO,
    "vidudala":      TokenKind.VIDUDALA,
    "tappu":         TokenKind.TAPPU,
    "tappudu":       TokenKind.TAPPUDU,

    # Concurrency
    "samaanakaalam": TokenKind.SAMAANAKAALAM,
    "vellu":         TokenKind.VELLU,
    "kaanal":        TokenKind.KAANAL,
    "nadumu":        TokenKind.NADUMU,

    # Range / iteration helpers
    "lo":            TokenKind.LO,
    "ki":            TokenKind.KI,
}


@dataclass(frozen=True)
class Token:
    """A single lexical token produced by the Akasha lexer."""
    kind:  TokenKind
    value: str
    line:  int
    col:   int

    def __repr__(self) -> str:
        return f"Token({self.kind.name}, {self.value!r}, {self.line}:{self.col})"
