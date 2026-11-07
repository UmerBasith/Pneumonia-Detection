"""Pull real code excerpts out of the project's source files (so listings never drift from the code)."""
import ast
import textwrap

from paths import ROOT


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def func(rel: str, name: str, cls: str | None = None) -> str:
    """Source of a top-level function/class, or a method of a class (dedented)."""
    src = read(rel)
    tree = ast.parse(src)
    nodes = tree.body
    if cls:
        nodes = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls).body
    node = next(n for n in nodes if getattr(n, "name", None) == name)
    lines = src.splitlines()
    start = node.lineno - 1
    if getattr(node, "decorator_list", None):
        start = min(d.lineno for d in node.decorator_list) - 1
    return textwrap.dedent("\n".join(lines[start:node.end_lineno]))


def between(rel: str, start: str, end: str, include_end: bool = True) -> str:
    """Lines from the first line containing `start` to the first later line containing `end`."""
    lines = read(rel).splitlines()
    i = next(k for k, l in enumerate(lines) if start in l)
    j = next(k for k in range(i + 1, len(lines)) if end in lines[k])
    return textwrap.dedent("\n".join(lines[i:j + (1 if include_end else 0)]))
