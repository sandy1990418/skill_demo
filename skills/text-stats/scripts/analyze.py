#!/usr/bin/env python3
"""Compute basic readability metrics for a text file.

Usage:
    python3 analyze.py <path-to-text-file>

Prints a JSON object to stdout with keys:
    words, sentences, avg_words_per_sentence, avg_word_length,
    unique_words, type_token_ratio, longest_sentence_words
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def analyze(text: str) -> dict:
    sentences = [s for s in re.split(r"[.!?]+\s+|[.!?]+$", text.strip()) if s.strip()]
    words = re.findall(r"\b[\w']+\b", text.lower())

    if not words or not sentences:
        return {"error": "empty or unparseable input"}

    total_chars = sum(len(w) for w in words)
    unique = len(set(words))
    sentence_word_counts = [len(re.findall(r"\b[\w']+\b", s)) for s in sentences]

    return {
        "words": len(words),
        "sentences": len(sentences),
        "avg_words_per_sentence": round(len(words) / len(sentences), 1),
        "avg_word_length": round(total_chars / len(words), 2),
        "unique_words": unique,
        "type_token_ratio": round(unique / len(words), 3),
        "longest_sentence_words": max(sentence_word_counts),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: analyze.py <path>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(json.dumps({"error": f"file not found: {path}"}))
        return 1
    print(json.dumps(analyze(path.read_text(encoding="utf-8")), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
