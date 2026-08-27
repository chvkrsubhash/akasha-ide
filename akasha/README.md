# Akasha Programming Language

> **Telugu-inspired. Globally readable. Secure by design.**

```akasha
cheppu("Namaste, Akasha!")

viluva peru = "Subhash"
viluva vayasu = 22

okavela vayasu >= 18 {
    cheppu(f"{peru} is a Pedda manishi (Adult)")
} lekapothe {
    cheppu(f"{peru} is a Chinna pilladu (Minor)")
}

karyam fibonacci(n) {
    okavela n <= 1 { phalitham n }
    phalitham fibonacci(n - 1) + fibonacci(n - 2)
}

prathi i lo 0..10 {
    cheppu(f"fib({i}) = {fibonacci(i)}")
}
```

---

## What is Akasha?

**Akasha** (Telugu: ఆకాశ, meaning *sky / ether / space*) is a new programming language with a unique identity:

- **Telugu-transliterated vocabulary** — keywords come from real Telugu words written in Latin characters
- **No Telugu Unicode required** — any developer can type Akasha source code on any keyboard
- **General-purpose** — from simple scripts to complex systems software
- **Safe by default** — memory safety, bounds checking, and secret protection built in
- **Beginner-friendly syntax** — readable, consistent, and expressive


---

## Quick Start

### Requirements
- Python 3.11+

### Run your first program

```bash
python -m akasha.cli.astra run examples/01_hello_world.akasha
```

### Interactive REPL

```bash
python -m akasha.cli.astra repl
```

### Check syntax without running

```bash
python -m akasha.cli.astra check myprogram.akasha
```

---

## Language at a Glance

### Variables
```akasha
viluva name = "Akasha"           -- mutable variable
sthiram MAX = 100              -- constant
rahasyam api_key = environment("API_KEY")  -- secret (never leaks)
```

### Types
```akasha
viluva n: Sankhya  = 42        -- integer
viluva f: Dasamsam = 3.14      -- float
viluva s: Padam    = "hello"   -- string
viluva b: Nijam    = nijam     -- boolean (true)
viluva x           = shunyam   -- null
```

### Conditions
```akasha
okavela score >= 90 {
    cheppu("A+")
} mariyu score >= 80 {
    cheppu("A")
} lekapothe {
    cheppu("Need to study more!")
}
```

### Loops
```akasha
-- for-each
prathi item lo ["manga", "arati", "nimma"] {
    cheppu(item)
}

-- range loop
prathi i lo 1..11 {
    cheppu(i)
}

-- while
viluva maarpu i = 0
alaa i < 10 {
    i = i + 1
}

-- infinite loop with break
loop {
    viluva input = adugu("Enter command: ")
    okavela input == "exit" { aapu }
}
```

### Functions
```akasha
karyam add(a: Sankhya, b: Sankhya): Sankhya {
    phalitham a + b
}

-- Default parameters
karyam greet(name: Padam = "World") {
    cheppu(f"Namaste, {name}!")
}

-- Closures
viluva square = muppu(x) => x * x
viluva doubled = [1,2,3].map(muppu(x) => x * 2)
```

### Match
```akasha
tirugu color {
    sthithi "erra"    => cheppu("Red")
    sthithi "pachcha" => cheppu("Green")
    sthithi "neelam"  => cheppu("Blue")
    default           => cheppu("Unknown")
}
```

### Collections
```akasha
viluva arr = [1, 2, 3, 4, 5]
viluva evens = arr.filter(muppu(x) => x % 2 == 0)
viluva doubled = arr.map(muppu(x) => x * 2)
viluva total = arr.reduce(muppu(acc, x) => acc + x, 0)

viluva map = {"key": "value", "score": 100}
```

---

## Telugu Keyword Reference

| Akasha Keyword | Telugu Meaning | English Equivalent |
|-------------|---------------|-------------------|
| `cheppu` | say/tell | print |
| `viluva` | value/variable | let/var |
| `sthiram` | fixed | const |
| `rahasyam` | secret | secret |
| `okavela` | if/when | if |
| `lekapothe` | otherwise | else |
| `mariyu` | and-also | else if |
| `alaa` | while/like that | while |
| `prathi` | each/every | for |
| `loop` | loop | loop |
| `aapu` | stop | break |
| `konasaginchu` | continue | continue |
| `karyam` | function/task | fn |
| `phalitham` | result/return | return |
| `muppu` | closure/wrap | lambda |
| `lo` | in/within | in |
| `tirugu` | match/check | match |
| `sthithi` | case/state | case |
| `nijam` | true/real | true |
| `abaddham` | false/wrong | false |
| `shunyam` | nothing/zero | null |
| `digumathi` | import/bring | import |
| `egumathi` | export/send | export |
| `rachana` | structure | struct |
| `asura` | unsafe | unsafe |

---

## Project Structure

```
akasha/
├── compiler/
│   ├── lexer/          Tokenizer (source → tokens)
│   │   ├── token.py    Token types and keyword table
│   │   └── lexer.py    Lexer implementation
│   ├── parser/         Recursive-descent parser (tokens → AST)
│   │   └── parser.py
│   ├── ast_nodes/      AST node definitions
│   │   └── nodes.py
│   ├── interpreter/    Tree-walking interpreter (v0.1 runtime)
│   │   ├── values.py   Akasha runtime value types
│   │   └── interpreter.py
│   └── stdlib/         Standard library modules
│       └── __init__.py (math, io, string, os, time)
├── cli/
│   └── astra.py        Command-line interface
├── tests/
│   ├── test_lexer.py       69 tests
│   ├── test_parser.py      50 tests
│   ├── test_interpreter.py 89 tests
│   └── test_integration.py 16 tests
├── examples/
│   ├── 01_hello_world.akasha
│   ├── 02_variables.akasha
│   ├── 03_conditions.akasha
│   ├── 04_functions.akasha
│   ├── 05_loops.akasha
│   └── 06_showcase.akasha
└── astra.py            Launcher script
```

---

## Running Tests

```bash
python -m pytest akasha/tests/ -v
```

Expected: **224 tests, 0 failures**

---

## CLI Reference

```
akasha run   <file.akasha>   Execute a Akasha source file
akasha check <file.akasha>   Parse and check without running
akasha repl                Start interactive REPL
akasha version             Show version information
akasha help                Show help
```

---

## Standard Library (v0.1)

### math
```akasha
digumathi math
cheppu(math.sqrt(16))     -- 4.0
cheppu(math.PI)           -- 3.14159...
cheppu(math.floor(3.7))   -- 3
```

### io
```akasha
digumathi io
viluva content = io.read("data.txt")
io.write("out.txt", "Hello!")
```

### string
```akasha
digumathi string
cheppu(string.repeat("ha", 3))   -- hahaha
```

### os
```akasha
digumathi os
cheppu(os.cwd())
viluva val = os.env("HOME")
```

---

## Security Features

- **`rahasyam`** — secret variables never leak through `cheppu()` or error messages
- **Bounds checking** — all array/string indexing is checked; no buffer overflows
- **`asura` blocks** — unsafe operations are explicitly marked
- **`environment()`** — discourages hard-coded secrets
- **No null dereferences** — use `Vikalpa[T]` instead of null where possible

---

## Roadmap

| Version | Status | Features |
|---------|--------|---------|
| v0.1 | ✅ Done | Interpreter, variables, functions, loops, conditions, CLI, REPL |
| v0.2 | Planned | Better type checking, modules, improved errors |
| v0.3 | Planned | Structs, enums, generics, pattern matching, Result/Option |
| v0.4 | Planned | Networking, HTTP, DNS, TLS, crypto |
| v0.5 | Planned | Security model, permissions, sandboxing |
| v0.6 | Planned | AI/ML tensor API |
| v0.7 | Planned | Native LLVM compiler |
| v1.0 | Planned | Stable release, package manager, tooling |

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

*Akasha — The language that speaks Telugu to the world.*
