"""
Akasha Desktop Code Editor & IDE (PC Native Application)
========================================================

A lightweight, zero-dependency desktop code editor and development environment
for the Akasha programming language built on Python's native Tkinter.
"""

from __future__ import annotations
import sys
import os
import io
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Ensure project root is in sys.path
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from .highlighter import SyntaxHighlighter, THEMES
from akasha.compiler.lexer.lexer import Lexer, LexerError
from akasha.compiler.parser.parser import Parser, ParseError
from akasha.compiler.bytecode.compiler import BytecodeCompiler
from akasha.compiler.bytecode.serializer import save_bytecode_file
from akasha.compiler.interpreter.interpreter import Interpreter
from akasha.compiler.interpreter.values import AkashaRuntimeError, ReturnSignal, _to_display_str
from akasha.runtime.vm import AkashaVM

DEFAULT_TEMPLATE = """-- Welcome to Akasha Desktop IDE!
-- Write, compile, and run Akasha programs on your PC.

cheppu("Namaste, Akasha PC IDE!")

viluva name = "Akasha"
viluva version = 1

cheppu(f"Running on {name} v{version}")

-- Function example: Factorial
karyam factorial(n: Sankhya): Sankhya {
    okavela n <= 1 {
        phalitham 1
    }
    phalitham n * factorial(n - 1)
}

cheppu(f"5! = {factorial(5)}")
cheppu(f"10! = {factorial(10)}")

-- Iteration example
cheppu("Fibonacci numbers:")
karyam fib(n) {
    okavela n <= 1 { phalitham n }
    phalitham fib(n - 1) + fib(n - 2)
}

prathi i lo 0..8 {
    cheppu(f"  fib({i}) = {fib(i)}")
}
"""

SAMPLE_PROGRAMS = {
    "01. Hello World": """-- Hello World in Akasha
cheppu("Namaste, World!")
cheppu("Welcome to the Akasha programming language.")
""",
    "02. Variables & Math": """-- Variables and Math
viluva a = 20
viluva b = 6
sthiram PI = 3.14159

cheppu(f"a + b = {a + b}")
cheppu(f"a * b = {a * b}")
cheppu(f"a / b = {a / b}")
cheppu(f"a ** b = {a ** b}")
""",
    "03. Conditionals": """-- Conditionals in Akasha
viluva score = 88

okavela score >= 90 {
    cheppu("Grade: A+ (Uttamam)")
} mariyu score >= 80 {
    cheppu("Grade: A (Baga undi)")
} lekapothe {
    cheppu("Grade: Needs practice")
}
""",
    "04. Loops & Range": """-- Loops & Ranges
cheppu("Counting 1 to 5:")
prathi i lo 1..6 {
    cheppu(f"  Item {i}")
}

-- While loop
viluva count = 1
alaa count <= 3 {
    cheppu(f"  While step: {count}")
    count = count + 1
}
""",
    "05. Bubble Sort": """-- Bubble Sort Algorithm
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

viluva nums = [64, 34, 25, 12, 22, 11, 90]
cheppu(f"Before: {nums}")
viluva sorted = bubble_sort(nums)
cheppu(f"After:  {sorted}")
"""
}


class AkashaIDE:
    """Main Desktop IDE Application."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Akasha Desktop IDE - [Untitled]")
        self.root.geometry("1100x720")
        self.root.minsize(800, 500)

        self.current_file: Optional[str] = None
        self.current_theme = "dark"

        self._setup_ui()
        self._setup_shortcuts()
        self._load_template()

    def _setup_ui(self) -> None:
        """Create the IDE layout and widgets."""
        # 1. Top Menu Bar
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="New File", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=lambda: self.editor.edit_undo())
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=lambda: self.editor.edit_redo())
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.editor.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.editor.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.editor.event_generate("<<Paste>>"))
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        # Run Menu
        run_menu = tk.Menu(self.menubar, tearoff=0)
        run_menu.add_command(label="Run Script", accelerator="F5", command=self.run_code)
        run_menu.add_command(label="Compile to Bytecode (.akb)", accelerator="Ctrl+B", command=self.compile_bytecode)
        run_menu.add_command(label="Check Syntax", accelerator="F7", command=self.check_syntax)
        run_menu.add_separator()
        run_menu.add_command(label="Clear Console", accelerator="Ctrl+L", command=self.clear_console)
        self.menubar.add_cascade(label="Run", menu=run_menu)

        # Theme Menu
        theme_menu = tk.Menu(self.menubar, tearoff=0)
        theme_menu.add_command(label="Dark Theme", command=lambda: self.apply_theme("dark"))
        theme_menu.add_command(label="Light Theme", command=lambda: self.apply_theme("light"))
        self.menubar.add_cascade(label="Theme", menu=theme_menu)

        # Help Menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="Akasha Language Docs", command=self.show_cheatsheet)
        help_menu.add_command(label="About Akasha IDE", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        # 2. Main Toolbar
        self.toolbar = tk.Frame(self.root, bg="#252526", height=36)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_style = {"bg": "#333333", "fg": "#ffffff", "activebackground": "#444444", "activeforeground": "#ffffff", "bd": 0, "padx": 10, "pady": 4, "font": ("Segoe UI", 9)}

        self.btn_run = tk.Button(self.toolbar, text="▶ Run (F5)", bg="#16a34a", fg="#ffffff", activebackground="#15803d", activeforeground="#ffffff", bd=0, padx=12, pady=4, font=("Segoe UI", 9, "bold"), command=self.run_code)
        self.btn_run.pack(side=tk.LEFT, padx=(6, 4), pady=4)

        self.btn_compile = tk.Button(self.toolbar, text="⚙ Compile (Ctrl+B)", command=self.compile_bytecode, **btn_style)
        self.btn_compile.pack(side=tk.LEFT, padx=4, pady=4)

        self.btn_check = tk.Button(self.toolbar, text="✓ Check (F7)", command=self.check_syntax, **btn_style)
        self.btn_check.pack(side=tk.LEFT, padx=4, pady=4)

        self.btn_clear = tk.Button(self.toolbar, text="Clear Console", command=self.clear_console, **btn_style)
        self.btn_clear.pack(side=tk.LEFT, padx=4, pady=4)

        # 3. Main Workspace Split (PanedWindow)
        self.paned_h = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#1e1e1e", bd=0, sashwidth=4)
        self.paned_h.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Sidebar: Sample Programs Library
        self.sidebar_frame = tk.Frame(self.paned_h, bg="#252526", width=200)
        self.sidebar_label = tk.Label(self.sidebar_frame, text="Samples Library", bg="#2d2d2d", fg="#cccccc", font=("Segoe UI", 9, "bold"), pady=6)
        self.sidebar_label.pack(side=tk.TOP, fill=tk.X)

        self.samples_listbox = tk.Listbox(self.sidebar_frame, bg="#252526", fg="#cccccc", selectbackground="#094771", selectforeground="#ffffff", bd=0, font=("Segoe UI", 9), highlightthickness=0)
        for name in SAMPLE_PROGRAMS.keys():
            self.samples_listbox.insert(tk.END, name)
        self.samples_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.samples_listbox.bind("<Double-Button-1>", self._on_sample_double_click)

        self.paned_h.add(self.sidebar_frame, minsize=140)

        # Vertical Split: Editor (Top) & Console (Bottom)
        self.paned_v = tk.PanedWindow(self.paned_h, orient=tk.VERTICAL, bg="#1e1e1e", bd=0, sashwidth=4)
        self.paned_h.add(self.paned_v, minsize=400)

        # Editor Frame
        self.editor_frame = tk.Frame(self.paned_v, bg="#1e1e1e")
        self.paned_v.add(self.editor_frame, minsize=200, height=440)

        # Line numbers gutter
        self.gutter = tk.Text(self.editor_frame, width=4, padx=4, pady=6, bg="#252526", fg="#858585", font=("Consolas", 11), bd=0, highlightthickness=0, state=tk.DISABLED)
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

        # Main Code Text Editor
        self.editor = tk.Text(self.editor_frame, wrap=tk.NONE, undo=True, font=("Consolas", 11), bg="#1e1e1e", fg="#d4d4d4", insertbackground="#569cd6", selectbackground="#264f78", bd=0, highlightthickness=0, padx=8, pady=6)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars for editor
        self.scrollbar_y = tk.Scrollbar(self.editor_frame, orient=tk.VERTICAL, command=self._scroll_both_y)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=self._update_scroll_y)

        # Bottom Console Output Frame
        self.console_frame = tk.Frame(self.paned_v, bg="#181818")
        self.paned_v.add(self.console_frame, minsize=120)

        self.console_header = tk.Frame(self.console_frame, bg="#252526", height=24)
        self.console_header.pack(side=tk.TOP, fill=tk.X)
        self.console_title = tk.Label(self.console_header, text="Terminal Output", bg="#252526", fg="#aaaaaa", font=("Segoe UI", 8, "bold"), padx=8)
        self.console_title.pack(side=tk.LEFT)
        self.exec_time_label = tk.Label(self.console_header, text="", bg="#252526", fg="#888888", font=("Consolas", 8), padx=8)
        self.exec_time_label.pack(side=tk.RIGHT)

        self.console = tk.Text(self.console_frame, bg="#0f172a", fg="#f8fafc", font=("Consolas", 10), bd=0, highlightthickness=0, padx=8, pady=6, state=tk.DISABLED)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.console_scroll = tk.Scrollbar(self.console_frame, command=self.console.yview)
        self.console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=self.console_scroll.set)

        # 4. Status Bar
        self.status_bar = tk.Frame(self.root, bg="#007acc", height=22)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_msg = tk.Label(self.status_bar, text="Ready", bg="#007acc", fg="#ffffff", font=("Segoe UI", 8), padx=8)
        self.status_msg.pack(side=tk.LEFT)

        self.cursor_pos = tk.Label(self.status_bar, text="Ln 1, Col 1", bg="#007acc", fg="#ffffff", font=("Segoe UI", 8), padx=8)
        self.cursor_pos.pack(side=tk.RIGHT)

        self.lang_badge = tk.Label(self.status_bar, text="Akasha v0.1 | UTF-8", bg="#007acc", fg="#ffffff", font=("Segoe UI", 8), padx=8)
        self.lang_badge.pack(side=tk.RIGHT)

        # Syntax Highlighter
        self.highlighter = SyntaxHighlighter(self.editor, theme_name=self.current_theme)

        # Bindings for editor
        self.editor.bind("<<Modified>>", self._on_text_modified)
        self.editor.bind("<KeyRelease>", self._on_key_release)
        self.editor.bind("<ButtonRelease-1>", self._update_cursor_pos)
        self.editor.bind("<Tab>", self._handle_tab)
        self.editor.bind("<Return>", self._handle_return)

    def _setup_shortcuts(self) -> None:
        self.root.bind("<F5>", lambda e: self.run_code())
        self.root.bind("<F7>", lambda e: self.check_syntax())
        self.root.bind("<Control-b>", lambda e: self.compile_bytecode())
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.root.bind("<Control-l>", lambda e: self.clear_console())

    def _load_template(self) -> None:
        self.editor.insert("1.0", DEFAULT_TEMPLATE)
        self.highlighter.highlight_all()
        self._update_gutter()

    def _scroll_both_y(self, *args: Any) -> None:
        self.editor.yview(*args)
        self.gutter.yview(*args)

    def _update_scroll_y(self, *args: Any) -> None:
        self.scrollbar_y.set(*args)
        self.gutter.yview_moveto(args[0])

    def _on_text_modified(self, event: Any = None) -> None:
        if self.editor.edit_modified():
            self.highlighter.highlight_all()
            self._update_gutter()
            self._update_cursor_pos()
            self.editor.edit_modified(False)

    def _on_key_release(self, event: Any = None) -> None:
        self._update_cursor_pos()

    def _update_gutter(self) -> None:
        line_count = int(self.editor.index("end-1c").split(".")[0])
        gutter_text = "\n".join(str(i) for i in range(1, line_count + 1))
        self.gutter.config(state=tk.NORMAL)
        self.gutter.delete("1.0", tk.END)
        self.gutter.insert("1.0", gutter_text)
        self.gutter.config(state=tk.DISABLED)

    def _update_cursor_pos(self, event: Any = None) -> None:
        idx = self.editor.index(tk.INSERT)
        line, col = idx.split(".")
        self.cursor_pos.config(text=f"Ln {line}, Col {int(col) + 1}")

    def _handle_tab(self, event: Any) -> str:
        self.editor.insert(tk.INSERT, "    ")
        return "break"

    def _handle_return(self, event: Any) -> str:
        # Auto-indent after '{'
        curr_line = self.editor.get("insert linestart", "insert")
        indent_level = len(curr_line) - len(curr_line.lstrip())
        extra = "    " if curr_line.rstrip().endswith("{") else ""
        self.editor.insert(tk.INSERT, "\n" + (" " * indent_level) + extra)
        self._update_gutter()
        return "break"

    def select_all(self) -> str:
        self.editor.tag_add("sel", "1.0", "end")
        return "break"

    def _on_sample_double_click(self, event: Any) -> None:
        selection = self.samples_listbox.curselection()
        if selection:
            name = self.samples_listbox.get(selection[0])
            code = SAMPLE_PROGRAMS.get(name, "")
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", code)
            self.highlighter.highlight_all()
            self._update_gutter()
            self.status_msg.config(text=f"Loaded Sample: {name}")

    def apply_theme(self, theme_name: str) -> None:
        self.current_theme = theme_name
        t = THEMES.get(theme_name, THEMES["dark"])
        self.editor.config(bg=t["bg"], fg=t["fg"], insertbackground=t["cursor"], selectbackground=t["select_bg"])
        self.gutter.config(bg=t["gutter_bg"], fg=t["gutter_fg"])
        self.highlighter.set_theme(theme_name)

    # ── Console Output ────────────────────────────────────────────────────────

    def log_console(self, text: str, is_error: bool = False) -> None:
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def clear_console(self) -> None:
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)
        self.exec_time_label.config(text="")
        self.status_msg.config(text="Console cleared")

    # ── File Operations ───────────────────────────────────────────────────────

    def new_file(self) -> None:
        self.editor.delete("1.0", tk.END)
        self.current_file = None
        self.root.title("Akasha Desktop IDE - [Untitled]")
        self._update_gutter()

    def open_file(self) -> None:
        filepath = filedialog.askopenfilename(
            filetypes=[("Akasha Source Files", "*.akasha *.aka *.teja"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                content = Path(filepath).read_text(encoding="utf-8")
                self.editor.delete("1.0", tk.END)
                self.editor.insert("1.0", content)
                self.current_file = filepath
                self.root.title(f"Akasha Desktop IDE - {Path(filepath).name}")
                self.highlighter.highlight_all()
                self._update_gutter()
                self.status_msg.config(text=f"Opened: {filepath}")
            except Exception as e:
                messagebox.showerror("Error Opening File", str(e))

    def save_file(self) -> bool:
        if self.current_file:
            try:
                content = self.editor.get("1.0", "end-1c")
                Path(self.current_file).write_text(content, encoding="utf-8")
                self.status_msg.config(text=f"Saved: {self.current_file}")
                return True
            except Exception as e:
                messagebox.showerror("Error Saving File", str(e))
                return False
        else:
            return self.save_file_as()

    def save_file_as(self) -> bool:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".akasha",
            filetypes=[("Akasha Source File", "*.akasha"), ("All Files", "*.*")]
        )
        if filepath:
            self.current_file = filepath
            self.root.title(f"Akasha Desktop IDE - {Path(filepath).name}")
            return self.save_file()
        return False

    # ── Compilation & Execution ───────────────────────────────────────────────

    def run_code(self) -> None:
        code = self.editor.get("1.0", "end-1c")
        if not code.trim() if hasattr(code, "trim") else not code.strip():
            return

        self.clear_console()
        self.status_msg.config(text="Running program...")

        def _worker():
            start_time = time.perf_counter()
            buf = io.StringIO()
            try:
                tokens = Lexer(code, filename=self.current_file or "<ide>").tokenize()
                program = Parser(tokens).parse()
                interp = Interpreter()
                # Run with stdout redirection
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    interp.execute(program)
                finally:
                    sys.stdout = old_stdout

                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                output = buf.getvalue()
                self.root.after(0, lambda: self._on_run_success(output, elapsed_ms))
            except Exception as e:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                self.root.after(0, lambda: self._on_run_error(str(e), elapsed_ms))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_run_success(self, output: str, elapsed_ms: float) -> None:
        self.log_console(output if output else "[Program finished with no output]")
        self.exec_time_label.config(text=f"Time: {elapsed_ms}ms")
        self.status_msg.config(text=f"Execution Finished ({elapsed_ms}ms)")

    def _on_run_error(self, err_msg: str, elapsed_ms: float) -> None:
        self.log_console(f"Execution Error:\n{err_msg}", is_error=True)
        self.exec_time_label.config(text=f"Time: {elapsed_ms}ms")
        self.status_msg.config(text="Execution encountered errors")

    def compile_bytecode(self) -> None:
        code = self.editor.get("1.0", "end-1c")
        if not code.strip():
            return

        out_path = filedialog.asksaveasfilename(
            defaultextension=".akb",
            filetypes=[("Akasha Bytecode File", "*.akb"), ("All Files", "*.*")]
        )
        if not out_path:
            return

        try:
            tokens = Lexer(code, filename=self.current_file or "<ide>").tokenize()
            program = Parser(tokens).parse()
            compiler = BytecodeCompiler(filename=self.current_file or "<ide>")
            chunk = compiler.compile(program)
            save_bytecode_file(chunk, out_path)
            self.log_console(f"Successfully compiled to: {out_path} ({len(chunk.instructions)} bytecode instructions)")
            self.status_msg.config(text=f"Compiled: {Path(out_path).name}")
            messagebox.showinfo("Compilation Complete", f"Compiled binary saved to:\n{out_path}")
        except Exception as e:
            self.log_console(f"Compilation Failed:\n{e}", is_error=True)
            messagebox.showerror("Compilation Error", str(e))

    def check_syntax(self) -> None:
        code = self.editor.get("1.0", "end-1c")
        if not code.strip():
            return
        try:
            tokens = Lexer(code, filename=self.current_file or "<ide>").tokenize()
            Parser(tokens).parse()
            self.status_msg.config(text="Syntax is valid!")
            messagebox.showinfo("Syntax Check", "Akasha syntax is valid! No errors found.")
        except Exception as e:
            self.log_console(f"Syntax Error:\n{e}", is_error=True)
            messagebox.showerror("Syntax Error", str(e))

    def show_cheatsheet(self) -> None:
        docs = """Akasha Language Cheatsheet:
------------------------------------------
cheppu("Hello")          -- Print
viluva x = 42            -- Variable
sthiram PI = 3.14159     -- Constant
okavela x > 0 { }        -- If
mariyu x == 0 { }        -- Else if
lekapothe { }            -- Else
prathi i lo 1..5 { }     -- For loop
alaa x > 0 { }           -- While loop
karyam add(a, b) { }     -- Function
phalitham result         -- Return
muppu(x) => x * x        -- Closure
"""
        messagebox.showinfo("Akasha Cheatsheet", docs)

    def show_about(self) -> None:
        about = "Akasha Desktop IDE v0.1.0\n\nThe Telugu-inspired programming language desktop development environment.\n\nAuthor: Akasha Team\nLicense: MIT"
        messagebox.showinfo("About Akasha IDE", about)


def launch_ide() -> None:
    """Launch the Akasha IDE desktop application."""
    root = tk.Tk()
    app = AkashaIDE(root)
    root.mainloop()


if __name__ == "__main__":
    launch_ide()
