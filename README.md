# Akasha Desktop IDE

<p align="center">
  <img src="logo.png" alt="Akasha Logo" width="200" />
</p>

> **Native Desktop Code Editor & Development Environment for Akasha**


A lightweight, zero-dependency desktop code editor and IDE designed specifically for the **Akasha** programming language.

---

## Features

- **Real-Time Syntax Highlighting**: Custom color coding for Akasha Telugu keywords (`cheppu`, `viluva`, `sthiram`, `karyam`, `okavela`, etc.), strings, numbers, types, and comments.
- **Synchronized Line Numbers & Gutter**: Line numbers gutter with smooth scrolling.
- **Auto-Indentation & Bracket Matching**: 4-space indentation and automatic indent after `{`.
- **Integrated Terminal Console**: Live execution output, error reports, and runtime benchmarks directly inside the editor.
- **1-Click Execution & Compilation**:
  - `F5` / `▶ Run`: Execute current script.
  - `Ctrl + B` / `⚙ Compile`: Compile source to binary bytecode (`.akb`).
  - `F7` / `✓ Check`: Validate syntax without running.
- **Built-in Samples Library**: Double-click any sample program (Hello World, Fibonacci, Bubble Sort, Loops) to load it instantly.
- **Theme Support**: Dark Theme (default) & Light Theme.

---

## Quick Start

### Requirements
- Python 3.10+ (Tkinter is included by default with standard Python on Windows/macOS)

### Launching the IDE

#### On Windows:
Double-click `akasha-ide.cmd` or run:
```cmd
akasha-ide
```

#### With Python:
```bash
python akasha_ide.py
```

#### Install Globally:
```bash
pip install -e .
akasha-ide
```

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`F5`** | **Run Program** |
| **`Ctrl + B`** | **Compile to Bytecode (`.akb`)** |
| **`F7`** | **Check Syntax** |
| **`Ctrl + N`** | New File |
| **`Ctrl + O`** | Open File |
| **`Ctrl + S`** | Save File |
| **`Ctrl + Shift + S`** | Save As... |
| **`Ctrl + L`** | Clear Console |
| **`Ctrl + Z`** / **`Ctrl + Y`** | Undo / Redo |

---

## License

MIT License
