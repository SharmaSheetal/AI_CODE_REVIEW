"""
parser.py — Parses Python source code into structured context using Tree-sitter.

Tree-sitter builds an Abstract Syntax Tree (AST) — a tree that describes WHAT
the code is (functions, classes, arguments) rather than what characters appear.
We use this to extract per-function context so the LLM review is specific to
individual functions, not just a blob of text.

Uses tree-sitter >= 0.25 API with the official tree-sitter-python grammar package.
"""

from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from dataclasses import dataclass, field
from typing import List

# Build the Language object once at module load — not on every parse call
PY_LANGUAGE = Language(tspython.language())


@dataclass
class FunctionContext:
    """All information extracted about a single function from the AST."""
    name: str
    start_line: int        # 1-indexed, matches GitHub line numbers
    end_line: int
    source: str            # Raw source text of the function body
    has_docstring: bool    # Whether the function has a docstring
    has_return: bool       # Whether the function contains a return statement
    parameter_names: List[str] = field(default_factory=list)


@dataclass
class ParsedFile:
    """Result of parsing one file — list of functions extracted from the AST."""
    filename: str
    functions: List[FunctionContext]
    parse_error: bool = False   # True if Tree-sitter couldn't parse the file


def _extract_text(node, source_bytes: bytes) -> str:
    """Extracts the raw source text for any AST node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")


def _extract_functions(root_node, source_bytes: bytes) -> List[FunctionContext]:
    """
    Walks the AST and collects every function definition.
    Tree-sitter node types for Python: 'function_definition', 'parameters', etc.
    """
    functions = []

    def walk(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            body_node = node.child_by_field_name("body")

            name = _extract_text(name_node, source_bytes) if name_node else "unknown"

            # Collect parameter names — handle plain, typed, and default variants:
            #   identifier          → def f(x)
            #   typed_parameter     → def f(x: int)
            #   default_parameter   → def f(x=0)
            #   typed_default_parameter → def f(x: int = 0)
            param_names = []
            if params_node:
                for child in params_node.children:
                    if child.type == "identifier":
                        param_names.append(_extract_text(child, source_bytes))
                    elif child.type in (
                        "typed_parameter",
                        "default_parameter",
                        "typed_default_parameter",
                    ):
                        # First child of these nodes is always the parameter name identifier
                        name_child = child.child_by_field_name("name") or (
                            child.children[0] if child.children else None
                        )
                        if name_child and name_child.type == "identifier":
                            param_names.append(_extract_text(name_child, source_bytes))

            # Check for docstring: first statement in body is a string expression
            has_docstring = False
            has_return = False
            if body_node:
                first_stmt = body_node.children[0] if body_node.children else None
                if first_stmt and first_stmt.type == "expression_statement":
                    expr = first_stmt.children[0] if first_stmt.children else None
                    if expr and expr.type in ("string", "concatenated_string"):
                        has_docstring = True

                # Walk body recursively to find any return statement
                def find_return(n):
                    nonlocal has_return
                    if n.type == "return_statement":
                        has_return = True
                    for child in n.children:
                        find_return(child)

                find_return(body_node)

            functions.append(FunctionContext(
                name=name,
                # Tree-sitter lines are 0-indexed; add 1 to match GitHub UI
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                source=_extract_text(node, source_bytes),
                has_docstring=has_docstring,
                has_return=has_return,
                parameter_names=param_names,
            ))

        for child in node.children:
            walk(child)

    walk(root_node)
    return functions


def parse_python_file(filename: str, source_code: str) -> ParsedFile:
    """
    Main entry point. Takes a filename and its full source, returns a ParsedFile
    with all extracted function contexts ready to send to the LLM.
    """
    parser = Parser(PY_LANGUAGE)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)

    # Tree-sitter always produces a tree even for invalid code; check for errors
    if tree.root_node.has_error:
        return ParsedFile(filename=filename, functions=[], parse_error=True)

    functions = _extract_functions(tree.root_node, source_bytes)
    return ParsedFile(filename=filename, functions=functions)
