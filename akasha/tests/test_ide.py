"""
Akasha Desktop IDE Unit Tests
=============================

Tests the syntax highlighter keywords, regex tagging, and theme definitions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from akasha.ide.highlighter import AKASHA_KEYWORDS, AKASHA_TYPES, AKASHA_BUILTINS, THEMES


class TestIDESyntaxHighlighter:
    def test_keywords_defined(self):
        assert "cheppu" in AKASHA_KEYWORDS
        assert "viluva" in AKASHA_KEYWORDS
        assert "sthiram" in AKASHA_KEYWORDS
        assert "karyam" in AKASHA_KEYWORDS
        assert "phalitham" in AKASHA_KEYWORDS
        assert "okavela" in AKASHA_KEYWORDS
        assert "lekapothe" in AKASHA_KEYWORDS
        assert "prathi" in AKASHA_KEYWORDS
        assert "alaa" in AKASHA_KEYWORDS
        assert "muppu" in AKASHA_KEYWORDS

    def test_types_defined(self):
        assert "Sankhya" in AKASHA_TYPES
        assert "Dasamsam" in AKASHA_TYPES
        assert "Padam" in AKASHA_TYPES
        assert "Nijam" in AKASHA_TYPES
        assert "Shunyam" in AKASHA_TYPES

    def test_themes_exist(self):
        assert "dark" in THEMES
        assert "light" in THEMES
        dark = THEMES["dark"]
        assert "bg" in dark
        assert "fg" in dark
        assert "keyword" in dark
        assert "string" in dark
