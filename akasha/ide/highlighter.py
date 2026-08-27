"""
Akasha Desktop IDE — Syntax Highlighter
========================================

Applies syntax highlighting tags to Tkinter Text widgets in real-time.
"""

from __future__ import annotations
import re
import tkinter as tk
from typing import Any

# Color theme configuration
THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#d4d4d4",
        "gutter_bg": "#252526",
        "gutter_fg": "#858585",
        "select_bg": "#264f78",
        "cursor": "#569cd6",
        "keyword": "#c586c0",     # Violet/Purple
        "type": "#4ec9b0",        # Cyan/Teal
        "string": "#ce9178",      # Orange/Brown
        "fstring": "#9cdcfe",     # Light Blue
        "number": "#b5cea8",      # Light Green
        "comment": "#6a9955",     # Green comment
        "builtin": "#dcdcaa",     # Yellow
        "function": "#dcdcaa",    # Yellow
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#1e293b",
        "gutter_bg": "#f8fafc",
        "gutter_fg": "#94a3b8",
        "select_bg": "#bfdbfe",
        "cursor": "#2563eb",
        "keyword": "#7c3aed",
        "type": "#0284c7",
        "string": "#15803d",
        "fstring": "#0f766e",
        "number": "#c2410c",
        "comment": "#94a3b8",
        "builtin": "#b91c1c",
        "function": "#1d4ed8",
    }
}

AKASHA_KEYWORDS = {
    "cheppu", "viluva", "sthiram", "rahasyam", "okavela", "lekapothe", "mariyu",
    "prathi", "lo", "alaa", "loop", "aapu", "konasaginchu", "karyam", "phalitham",
    "muppu", "tirugu", "sthithi", "nijam", "abaddham", "shunyam", "rachana",
    "enum", "lakshanam", "adugu", "nerpu", "asura", "digumathi", "egumathi",
    "vethuku", "default", "pariksha", "pattu", "antham", "visuru", "async", "aagu"
}

AKASHA_TYPES = {
    "Sankhya", "Dasamsam", "Padam", "Nijam", "Shunyam", "Vikalpa", "Phalitham",
    "Gumpu", "Naksha", "Janta", "Byte", "Patrika"
}

AKASHA_BUILTINS = {
    "parimaanam", "type_of", "range", "adugu", "Undu", "Ledu", "Sari", "Tappu"
}


class SyntaxHighlighter:
    """Manages syntax coloring for a Tkinter Text widget."""

    def __init__(self, text_widget: tk.Text, theme_name: str = "dark") -> None:
        self.text = text_widget
        self.theme = THEMES.get(theme_name, THEMES["dark"])
        self._setup_tags()

    def set_theme(self, theme_name: str) -> None:
        self.theme = THEMES.get(theme_name, THEMES["dark"])
        self._setup_tags()
        self.highlight_all()

    def _setup_tags(self) -> None:
        """Configure Tkinter text tags with theme colors."""
        t = self.theme
        self.text.tag_configure("keyword", foreground=t["keyword"], font=("Consolas", 11, "bold"))
        self.text.tag_configure("type", foreground=t["type"], font=("Consolas", 11, "bold"))
        self.text.tag_configure("string", foreground=t["string"])
        self.text.tag_configure("fstring", foreground=t["fstring"])
        self.text.tag_configure("number", foreground=t["number"])
        self.text.tag_configure("comment", foreground=t["comment"], font=("Consolas", 11, "italic"))
        self.text.tag_configure("builtin", foreground=t["builtin"])
        self.text.tag_configure("function", foreground=t["function"])

    def clear_tags(self) -> None:
        for tag in ("keyword", "type", "string", "fstring", "number", "comment", "builtin", "function"):
            self.text.tag_remove(tag, "1.0", tk.END)

    def highlight_all(self) -> None:
        """Run full syntax highlighting pass over the entire document."""
        self.clear_tags()
        content = self.text.get("1.0", tk.END)
        lines = content.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            self._highlight_line(line, line_idx)

    def _highlight_line(self, line: str, line_idx: int) -> None:
        i = 0
        n = len(line)

        while i < n:
            # Comments: -- or //
            if line[i:i+2] in ("--", "//"):
                self._apply_tag("comment", line_idx, i, n)
                break

            # F-string literal: f"..." or f'...'
            if line[i] == "f" and i + 1 < n and line[i+1] in ('"', "'"):
                quote = line[i+1]
                start = i
                end = i + 2
                while end < n and line[end] != quote:
                    if line[end] == "\\" and end + 1 < n:
                        end += 2
                    else:
                        end += 1
                if end < n: end += 1
                self._apply_tag("fstring", line_idx, start, end)
                i = end
                continue

            # Standard string literal: "..." or '...'
            if line[i] in ('"', "'"):
                quote = line[i]
                start = i
                end = i + 1
                while end < n and line[end] != quote:
                    if line[end] == "\\" and end + 1 < n:
                        end += 2
                    else:
                        end += 1
                if end < n: end += 1
                self._apply_tag("string", line_idx, start, end)
                i = end
                continue

            # Numbers (Hex or Decimal)
            if line[i].isdigit():
                start = i
                end = i
                if line[i:i+2].lower() == "0x":
                    end += 2
                    while end < n and (line[end].isalnum() or line[end] == "_"):
                        end += 1
                else:
                    while end < n and (line[end].isdigit() or line[end] in "._"):
                        end += 1
                self._apply_tag("number", line_idx, start, end)
                i = end
                continue

            # Identifiers, keywords, functions
            if line[i].isalpha() or line[i] == "_":
                start = i
                end = i
                while end < n and (line[end].isalnum() or line[end] == "_"):
                    end += 1
                word = line[start:end]

                if word in AKASHA_KEYWORDS:
                    self._apply_tag("keyword", line_idx, start, end)
                elif word in AKASHA_TYPES:
                    self._apply_tag("type", line_idx, start, end)
                elif word in AKASHA_BUILTINS:
                    self._apply_tag("builtin", line_idx, start, end)
                elif end < n and line[end] == "(":
                    self._apply_tag("function", line_idx, start, end)

                i = end
                continue

            i += 1

    def _apply_tag(self, tag_name: str, line: int, start_col: int, end_col: int) -> None:
        start = f"{line}.{start_col}"
        end = f"{line}.{end_col}"
        self.text.tag_add(tag_name, start, end)
